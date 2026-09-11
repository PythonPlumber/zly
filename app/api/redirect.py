import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db, get_redis_client
from app.core.security import validate_private_url
from app.core.user_agent import extract_domain, parse_user_agent
from app.core.logging import get_logger
from app.db import get_session_factory
from app.services.ab_service import list_variants, select_variant
from app.services.link_service import get_link_by_code

logger = get_logger(__name__)


async def _fire_webhooks(workspace_id: str, event: str, payload: dict) -> None:
    from app.services.webhook_service import trigger_webhooks
    factory = get_session_factory()
    async with factory() as session:
        try:
            await trigger_webhooks(session, workspace_id, event, payload)
            await session.commit()
        except Exception:
            await session.rollback()


router = APIRouter()


@router.get("/{short_code}")
async def redirect(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis_client),
):
    host = request.headers.get("host", "").split(":")[0]
    if host and host not in ("localhost", settings.default_domain.split(":")[0]):
        from app.services.domain_service import get_workspace_by_domain
        ws_id = await get_workspace_by_domain(db, host)
        if ws_id:
            from app.services.link_service import get_links_all
            all_links = await get_links_all(db, ws_id)
            for l in all_links:
                if l.short_code == short_code:
                    link = l
                    break

    try:
        cached_url = await redis.get(f"link:v2:{short_code}")
        if cached_url:
            try:
                validate_private_url(cached_url)
            except ValueError:
                logger.warning("Cached URL is private, falling back to DB", extra={"short_code": short_code, "cached_url": cached_url})
                cached_url = None
        if cached_url:
            return Response(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"location": cached_url},
            )
    except Exception as exc:
        logger.warning("Redis get failed, falling back to DB", extra={"short_code": short_code, "error": str(exc)})

    link = await get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    if not link.is_active or getattr(link, "is_archived", False):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link is inactive")

    now = datetime.now(timezone.utc)
    if link.activate_at and link.activate_at > now:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not yet active")
    if link.expires_at and link.expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")
    # Max clicks guard
    if getattr(link, "max_clicks", None):
        from sqlalchemy import func, select
        from app.models.click import Click
        cnt = await db.execute(select(func.count()).select_from(Click).where(Click.link_id == link.id))
        if (cnt.scalar() or 0) >= link.max_clicks:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has reached its click limit")

    if link.password_hash:
        password = request.query_params.get("password", "")
        from app.core.security import verify_password as check_pw
        if not password or not check_pw(password, link.password_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Password required",
                headers={"X-Link-Id": link.id, "X-Require-Password": "true"},
            )

    # Smart rules evaluation (geo/device/os/referrer)
    try:
        from app.services.link_rule_service import get_rules, evaluate_rules
        from app.services.geoip_service import resolve_ip as _resolve_ip
        rules = await get_rules(db, link.id)
        if rules:
            ip_for_geo = request.client.host if request.client else ""
            ctx = {}
            try:
                geo = await _resolve_ip(ip_for_geo) if ip_for_geo else None
                if geo:
                    ctx["country"] = geo.get("country")
                    ctx["city"] = geo.get("city")
            except Exception:
                pass
            ua_for_rules = request.headers.get("user-agent", "")
            parsed_for_rules = parse_user_agent(ua_for_rules)
            ctx["device"] = parsed_for_rules.get("device_type")
            ctx["os"] = parsed_for_rules.get("os")
            ctx["referrer"] = request.headers.get("referer") or request.headers.get("referrer")
            ctx["accept_language"] = request.headers.get("accept-language")
            matched = evaluate_rules(rules, ctx)
            if matched:
                target_url = matched
                selected_variant = None
                # Skip variant selection if rule matched
                variants = []
            else:
                # No rule matched, fall through to variant/primary
                variants_list = await list_variants(db, link.id)
                variants, _, _ = variants_list if isinstance(variants_list, tuple) else (variants_list, 0, False)
                target_url = link.destination_url
                selected_variant = None
                if variants:
                    selected_variant = select_variant(variants)
                    if selected_variant:
                        target_url = selected_variant.destination_url
        else:
            variants_list = await list_variants(db, link.id)
            variants, _, _ = variants_list if isinstance(variants_list, tuple) else (variants_list, 0, False)
            target_url = link.destination_url
            selected_variant = None
            if variants:
                selected_variant = select_variant(variants)
                if selected_variant:
                    target_url = selected_variant.destination_url
    except Exception:
        variants_list = await list_variants(db, link.id)
        variants, _, _ = variants_list if isinstance(variants_list, tuple) else (variants_list, 0, False)
        target_url = link.destination_url
        selected_variant = None
        if variants:
            selected_variant = select_variant(variants)
            if selected_variant:
                target_url = selected_variant.destination_url

    try:
        validate_private_url(target_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    try:
        has_rules = False
        try:
            from app.services.link_rule_service import get_rules as _gr
            _r = await _gr(db, link.id)
            has_rules = bool(_r)
        except Exception:
            pass
        cacheable = not link.password_hash and not link.expires_at and not variants and not has_rules and not getattr(link, "is_archived", False) and not getattr(link, "max_clicks", None)
        if cacheable:
            await redis.set(f"link:v2:{short_code}", target_url, ex=300)
    except Exception as exc:
        logger.warning("Redis set failed, cache will be cold", extra={"short_code": short_code, "error": str(exc)})

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")
    referer = request.headers.get("referer")
    parsed = parse_user_agent(ua)

    try:
        from app.core.arq_pool import get_arq_pool
        pool = await get_arq_pool()
        await pool.enqueue_job(
            "process_click",
            link_id=link.id,
            ip=ip,
            user_agent=ua,
            referrer=referer,
            variant_id=selected_variant.id if selected_variant else None,
        )
    except Exception as exc:
        logger.warning("Failed to enqueue click job, recording synchronously", extra={"error": str(exc)})
        from app.services.click_service import record_click
        await record_click(
            db, link.id, ip, ua, referer,
            variant_id=selected_variant.id if selected_variant else None,
        )

    asyncio.create_task(
        _fire_webhooks(
            link.workspace_id,
            "click.created",
            {
                "event": "click.created",
                "link_id": link.id,
                "short_code": link.short_code,
                "destination_url": target_url,
                "variant_id": selected_variant.id if selected_variant else None,
                "browser": parsed["browser"],
                "os": parsed["os"],
                "device_type": parsed["device_type"],
                "referrer_domain": extract_domain(referer),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    )

    return Response(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"location": target_url},
    )
