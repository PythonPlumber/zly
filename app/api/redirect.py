import asyncio
import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, get_redis_client
from app.core.user_agent import extract_domain, parse_user_agent
from app.core.logging import get_logger
logger = get_logger(__name__)
from app.db import get_session_factory
from app.models.click import Click
from app.services.ab_service import list_variants, select_variant
from app.services.link_service import get_link_by_code


async def _fire_webhooks(workspace_id: str, event: str, payload: dict) -> None:
    from app.services.webhook_service import trigger_webhooks
    factory = get_session_factory()
    async with factory() as session:
        try:
            await trigger_webhooks(session, workspace_id, event, payload)
            await session.commit()
        except Exception:
            await session.rollback()


async def _check_expiry_on_redirect(workspace_id: str) -> None:
    from app.services.notification_service import check_expiring_links
    factory = get_session_factory()
    async with factory() as session:
        try:
            await check_expiring_links(session, workspace_id)
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
    try:
        cached_url = await redis.get(f"link:{short_code}")
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
    if not link.is_active:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link is inactive")

    now = datetime.now(timezone.utc)
    if link.activate_at and link.activate_at > now:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not yet active")
    if link.expires_at and link.expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")

    if link.password_hash:
        password = request.query_params.get("password", "")
        from app.core.security import verify_password as check_pw
        if not password or not check_pw(password, link.password_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Password required",
                headers={"X-Link-Id": link.id, "X-Require-Password": "true"},
            )

    variants = await list_variants(db, link.id)
    target_url = link.destination_url
    selected_variant = None
    if variants:
        selected_variant = select_variant(variants)
        if selected_variant:
            target_url = selected_variant.destination_url

    try:
        await redis.set(f"link:{short_code}", target_url)
    except Exception as exc:
        logger.warning("Redis set failed, cache will be cold", extra={"short_code": short_code, "error": str(exc)})

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")
    referer = request.headers.get("referer")
    parsed = parse_user_agent(ua)

    click = Click(
        link_id=link.id,
        ip_hash=hashlib.sha256(ip.encode()).hexdigest(),
        user_agent=ua,
        referrer=referer,
        referrer_domain=extract_domain(referer),
        browser=parsed["browser"],
        browser_version=parsed["browser_version"],
        os=parsed["os"],
        device_type=parsed["device_type"],
        variant_id=selected_variant.id if selected_variant else None,
    )
    db.add(click)

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

    asyncio.create_task(_check_expiry_on_redirect(link.workspace_id))

    return Response(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"location": target_url},
    )
