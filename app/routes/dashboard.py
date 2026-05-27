from datetime import datetime, timezone
from html import escape as h

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import decode_access_token as decode_jwt, get_current_user_from_cookie as get_current_user
from app.models.user import User
from app.services.bio_service import get_bio_link, get_bio_page, get_bio_page_by_slug
from app.services.link_service import get_link_by_id, get_links
from app.services.workspace_service import create_workspace, get_workspace, get_workspaces_for_user
from app.services.webhook_service import get_webhooks
from app.services.domain_service import list_workspace_domains
from app.services.tag_service import get_tags
from app.services.api_key_service import list_api_keys
from app.services.invite_service import list_invites, list_members
from app.services.analytics_service import get_workspace_summary
from app.services.session_service import list_sessions
from app.services.notification_service import check_expiring_links
from app.services.ab_service import get_variant, list_variants
import httpx
from app.services.email_campaign_service import list_contacts, list_templates, get_template, list_campaigns, get_campaign, update_campaign_stats

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/index.html",
        {"user": current_user, "default_ws": default_ws, "workspaces": workspaces},
    )


@router.get("/dashboard/links", response_class=HTMLResponse)
async def links_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/links.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/links/{link_id}", response_class=HTMLResponse)
async def link_detail_page(
    request: Request,
    link_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404)
    ws = await get_workspace(db, link.workspace_id)
    if not ws or ws.owner_id != current_user.id:
        raise HTTPException(status_code=403)
    return templates.TemplateResponse(
        request, "dashboard/link_detail.html",
        {"user": current_user, "link": link},
    )


@router.get("/dashboard/bio", response_class=HTMLResponse)
async def bio_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    bio = None
    if default_ws:
        bio = await get_bio_page(db, default_ws.id)
    return templates.TemplateResponse(
        request, "dashboard/bio.html",
        {"user": current_user, "bio": bio, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request, "dashboard/settings.html",
        {"user": current_user},
    )


@router.get("/dashboard/domains", response_class=HTMLResponse)
async def domains_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/domains.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/email", response_class=HTMLResponse)
async def email_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/email.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/api-keys", response_class=HTMLResponse)
async def api_keys_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/api_keys.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/webhooks", response_class=HTMLResponse)
async def webhooks_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/webhooks.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/tags", response_class=HTMLResponse)
async def tags_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/tags.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/invites", response_class=HTMLResponse)
async def invites_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "dashboard/invites.html",
        {"user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/workspaces", response_class=HTMLResponse)
async def workspaces_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    return templates.TemplateResponse(
        request, "dashboard/workspaces.html",
        {"user": current_user, "workspaces": workspaces},
    )


@router.get("/dashboard/workspaces/list", response_class=HTMLResponse)
async def workspaces_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    return templates.TemplateResponse(
        request, "partials/workspace_list.html",
        {"user": current_user, "workspaces": workspaces},
    )


@router.get("/dashboard/workspaces/new-form", response_class=HTMLResponse)
async def workspace_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request, "partials/workspace_form.html",
        {},
    )


@router.get("/dashboard/workspaces/{workspace_id}/edit-form", response_class=HTMLResponse)
async def workspace_edit_form(
    request: Request,
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await get_workspace(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/workspace_form.html",
        {"workspace": ws},
    )


@router.get("/dashboard/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")
    return templates.TemplateResponse(
        request, "dashboard/admin_stats.html",
        {"user": current_user},
    )


@router.get("/dashboard/admin/audit", response_class=HTMLResponse)
async def audit_logs_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")
    return templates.TemplateResponse(
        request, "dashboard/audit_logs.html",
        {"user": current_user},
    )


@router.get("/bio/{slug}", response_class=HTMLResponse)
async def public_bio_page(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    bio = await get_bio_page_by_slug(db, slug)
    if not bio or not bio.is_published:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "bio/public.html",
        {"bio": bio},
    )


# ---- HTMX Partial Routes ----

@router.get("/dashboard/summary", response_class=HTMLResponse)
async def dashboard_summary(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse("")
    summary = await get_workspace_summary(db, default_ws.id, 7)
    return templates.TemplateResponse(
        request, "partials/workspace_summary.html",
        summary.model_dump(),
    )


@router.get("/dashboard/links/list", response_class=HTMLResponse)
async def links_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="6" style="text-align:center;padding:3rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO WORKSPACE</td></tr>')
    now = datetime.now(timezone.utc)
    links, total, has_next = await get_links(db, default_ws.id, page=1, page_size=50)
    rows = []
    for link in links:
        badge_html = ''
        if link.is_active:
            badge_html = '<span class="zly-badge zly-badge-active">Active</span>'
        else:
            badge_html = '<span class="zly-badge zly-badge-hidden">Inactive</span>'
        if link.expires_at:
            delta = (link.expires_at - now).total_seconds()
            if delta <= 0:
                badge_html += ' <span class="zly-badge zly-badge-danger">Expired</span>'
            elif delta <= 7 * 86400:
                badge_html += ' <span class="zly-badge zly-badge-warning" style="background:rgba(255,107,53,0.12)!important;color:#ff6b35!important;">Expiring</span>'
        if link.password_hash:
            badge_html += ' <span class="zly-badge zly-badge-warning">Protected</span>'
        health_badge = ''
        if link.is_active:
            try:
                resp = await httpx.AsyncClient(timeout=2.0).head(link.destination_url, follow_redirects=True)
                status_code = resp.status_code
                if 200 <= status_code < 400:
                    health_badge = ' <span class="zly-badge zly-badge-active" style="font-size:0.5rem;">✓ Online</span>'
                else:
                    health_badge = f' <span class="zly-badge zly-badge-danger" style="font-size:0.5rem;">✗ {status_code}</span>'
            except Exception:
                health_badge = ' <span class="zly-badge zly-badge-warning" style="font-size:0.5rem;">⚠ Timeout</span>'
        rows.append(f'''<tr>
            <td style="max-width:12rem;"><code style="font-family:Space Mono,monospace;font-size:0.75rem;color:var(--zly-emerald);cursor:pointer;" onclick="copyToClipboard('/{h(link.short_code)}')">/{h(link.short_code)}</code></td>
            <td style="max-width:16rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{h(link.destination_url)}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.75rem;">{link.clicks or 0}</td>
            <td>{badge_html}{health_badge}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-muted);">{link.created_at.strftime('%Y-%m-%d') if link.created_at else ''}</td>
            <td style="text-align:right;white-space:nowrap;">
                <a href="/dashboard/links/{link.id}" class="zly-btn zly-btn-secondary" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;">Analytics</a>
                <button class="zly-btn zly-btn-secondary" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-get="/dashboard/links/{link.id}/edit-form" hx-target="#edit-link-modal" hx-swap="innerHTML">Edit</button>
                <button class="zly-btn zly-btn-danger" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-delete="/api/v1/workspaces/{default_ws.id}/links/{link.id}" hx-target="#links-tbody" hx-swap="outerHTML" hx-confirm="Delete this link?">Delete</button>
            </td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="6" style="text-align:center;padding:3rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO LINKS YET. CREATE ONE.</td></tr>')
    return HTMLResponse("".join(rows))


@router.get("/dashboard/links/new-form", response_class=HTMLResponse)
async def link_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/link_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/links/import-form", response_class=HTMLResponse)
async def link_import_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/bulk_import_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/links/check-expiring", response_class=HTMLResponse)
async def link_check_expiring(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<div style="color:var(--zly-muted);font-size:0.65rem;">NO WORKSPACE</div>')
    result = await check_expiring_links(db, default_ws.id, within_hours=168)
    count = result.get("notified", 0)
    links = result.get("links", [])
    if not links:
        return HTMLResponse('<div style="color:var(--zly-emerald);font-size:0.65rem;">✅ No links expiring within 7 days.</div>')
    rows = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid var(--zly-line);font-size:0.6rem;">'
        f'<span style="font-family:Space Mono,monospace;">/{h(l.get("short_code",""))}</span>'
        f'<span style="color:var(--zly-muted);">{l.get("expires_at","")}</span>'
        f'</div>' for l in links
    )
    return HTMLResponse(
        f'<div style="padding:0.5rem 0;font-size:0.65rem;">'
        f'<div style="margin-bottom:0.5rem;"><span style="color:#ff6b35;">⚠</span> {count} links expiring within 7 days:</div>'
        f'{rows}</div>'
    )


@router.get("/dashboard/links/{link_id}/edit-form", response_class=HTMLResponse)
async def link_edit_form(
    request: Request,
    link_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/link_form.html",
        {"link": link, "workspace_id": link.workspace_id},
    )


@router.get("/dashboard/webhooks/list", response_class=HTMLResponse)
async def webhooks_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="5" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    webhooks, _, _ = await get_webhooks(db, default_ws.id)
    rows = []
    for w in webhooks:
        events_str = w.events if w.events else "all"
        rows.append(f'''<tr>
            <td style="font-weight:500;font-family:Space Grotesk,sans-serif;font-size:0.75rem;">{w.name}</td>
            <td style="max-width:16rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-muted);">{w.url}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;">{events_str}</td>
            <td>{'<span class="zly-badge zly-badge-active">Active</span>' if w.is_active else '<span class="zly-badge zly-badge-hidden">Inactive</span>'}</td>
            <td style="text-align:right;white-space:nowrap;">
                <button class="zly-btn zly-btn-secondary" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-get="/dashboard/webhooks/{w.id}/edit-form" hx-target="#webhook-form-modal" hx-swap="innerHTML">Edit</button>
                <button class="zly-btn zly-btn-danger" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-delete="/api/v1/workspaces/{default_ws.id}/webhooks/{w.id}" hx-target="closest tr" hx-swap="outerHTML" hx-confirm="Delete this webhook?">Delete</button>
            </td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="5" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO WEBHOOKS YET.</td></tr>')
    return HTMLResponse("".join(rows))


@router.get("/dashboard/webhooks/new-form", response_class=HTMLResponse)
async def webhook_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/webhook_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/webhooks/{webhook_id}/edit-form", response_class=HTMLResponse)
async def webhook_edit_form(
    request: Request,
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.webhook_service import get_webhook
    webhook = await get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/webhook_form.html",
        {"webhook": webhook, "workspace_id": webhook.workspace_id},
    )


@router.get("/dashboard/domains/list", response_class=HTMLResponse)
async def domains_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="4" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    domains, _, _ = await list_workspace_domains(db, default_ws.id)
    rows = []
    for d in domains:
        status_badge = '<span class="zly-badge zly-badge-active">Verified</span>' if d.is_verified else '<span class="zly-badge zly-badge-warning">Pending</span>'
        verify_btn = ''
        if not d.is_verified:
            verify_btn = f'<button class="zly-btn zly-btn-secondary" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-post="/api/v1/workspaces/{default_ws.id}/domains/{d.id}/verify" hx-target="closest tr" hx-swap="outerHTML">Verify</button>'
        rows.append(f'''<tr>
            <td style="font-family:Space Mono,monospace;font-size:0.75rem;color:var(--zly-emerald);">{d.domain}</td>
            <td>{status_badge}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-muted);">{d.created_at.strftime('%Y-%m-%d') if d.created_at else ''}</td>
            <td style="text-align:right;white-space:nowrap;">{verify_btn}
                <button class="zly-btn zly-btn-danger" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-delete="/api/v1/workspaces/{default_ws.id}/domains/{d.id}" hx-target="closest tr" hx-swap="outerHTML" hx-confirm="Delete this domain?">Delete</button>
            </td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="4" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO DOMAINS YET.</td></tr>')
    return HTMLResponse("".join(rows))


@router.get("/dashboard/domains/new-form", response_class=HTMLResponse)
async def domain_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/domain_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/tags/list", response_class=HTMLResponse)
async def tags_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="4" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    tags, _, _ = await get_tags(db, default_ws.id)
    rows = []
    for t in tags:
        color_hex = t.color or '#6366f1'
        rows.append(f'''<tr>
            <td style="font-weight:500;font-family:Space Grotesk,sans-serif;font-size:0.75rem;">{h(t.name)}</td>
            <td><span style="display:inline-block;width:0.75rem;height:0.75rem;background:{color_hex};vertical-align:middle;margin-right:0.25rem;"></span><code style="font-family:Space Mono,monospace;font-size:0.65rem;color:var(--zly-muted);">{h(color_hex)}</code></td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-muted);">{t.created_at.strftime('%Y-%m-%d') if t.created_at else ''}</td>
            <td style="text-align:right;white-space:nowrap;">
                <button class="zly-btn zly-btn-secondary" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-get="/dashboard/tags/{t.id}/edit-form" hx-target="#tag-form-modal" hx-swap="innerHTML">Edit</button>
                <button class="zly-btn zly-btn-danger" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-delete="/api/v1/workspaces/{default_ws.id}/tags/{t.id}" hx-target="closest tr" hx-swap="outerHTML" hx-confirm="Delete this tag?">Delete</button>
            </td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="4" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO TAGS YET.</td></tr>')
    return HTMLResponse("".join(rows))


@router.get("/dashboard/tags/new-form", response_class=HTMLResponse)
async def tag_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/tag_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/tags/{tag_id}/edit-form", response_class=HTMLResponse)
async def tag_edit_form(
    request: Request,
    tag_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.tag_service import get_tag
    tag = await get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/tag_form.html",
        {"tag": tag, "workspace_id": tag.workspace_id},
    )


@router.get("/dashboard/api-keys/list", response_class=HTMLResponse)
async def api_keys_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="6" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    keys, _, _ = await list_api_keys(db, default_ws.id)
    rows = []
    for k in keys:
        last_used = k.last_used_at.strftime('%Y-%m-%d') if k.last_used_at else 'Never'
        rows.append(f'''<tr>
            <td style="font-weight:500;font-family:Space Grotesk,sans-serif;font-size:0.75rem;">{h(k.name)}</td>
            <td><code style="font-family:Space Mono,monospace;font-size:0.65rem;color:var(--zly-muted);cursor:pointer;" onclick="copyToClipboard('{h(k.prefix)}...')">{h(k.prefix)}••••••••</code></td>
            <td style="font-family:Space Mono,monospace;font-size:0.65rem;color:var(--zly-muted);">{h(k.permissions or 'all')}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-muted);">{last_used}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-muted);">{k.created_at.strftime('%Y-%m-%d') if k.created_at else ''}</td>
            <td style="text-align:right;white-space:nowrap;">
                <button class="zly-btn zly-btn-secondary" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-get="/dashboard/api-keys/{k.id}/edit-form" hx-target="#key-form-modal" hx-swap="innerHTML">Edit</button>
                <button class="zly-btn zly-btn-danger" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-delete="/api/v1/workspaces/{default_ws.id}/api-keys/{k.id}" hx-target="closest tr" hx-swap="outerHTML" hx-confirm="Revoke this API key?">Revoke</button>
            </td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="6" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO API KEYS YET.</td></tr>')
    return HTMLResponse("".join(rows))


@router.get("/dashboard/api-keys/new-form", response_class=HTMLResponse)
async def api_key_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/api_key_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/api-keys/{key_id}/edit-form", response_class=HTMLResponse)
async def api_key_edit_form(
    request: Request,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.api_key_service import get_api_key
    key = await get_api_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/api_key_form.html",
        {"key": key, "workspace_id": key.workspace_id},
    )


@router.get("/dashboard/invites/list", response_class=HTMLResponse)
async def invites_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="5" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    invites, _, _ = await list_invites(db, default_ws.id)
    rows = []
    for inv in invites:
        status_class = ''
        if inv.status == 'pending': status_class = 'zly-badge-warning'
        elif inv.status == 'accepted': status_class = 'zly-badge-active'
        else: status_class = 'zly-badge-hidden'
        cancel_btn = ''
        if inv.status == 'pending':
            cancel_btn = f'<button class="zly-btn zly-btn-danger" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-delete="/api/v1/workspaces/{default_ws.id}/invites/{inv.id}" hx-target="closest tr" hx-swap="outerHTML" hx-confirm="Cancel this invite?">Cancel</button>'
        rows.append(f'''<tr>
            <td style="font-family:Space Mono,monospace;font-size:0.75rem;">{h(inv.email)}</td>
            <td><span class="zly-badge zly-badge-role">{h(inv.role)}</span></td>
            <td><span class="zly-badge {status_class}">{inv.status.title()}</span></td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-muted);">{inv.created_at.strftime('%Y-%m-%d') if inv.created_at else ''}</td>
            <td style="text-align:right;white-space:nowrap;">{cancel_btn}</td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="5" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO INVITES YET.</td></tr>')
    return HTMLResponse("".join(rows))


@router.get("/dashboard/invites/members", response_class=HTMLResponse)
async def members_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="4" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    members, _, _ = await list_members(db, default_ws.id)
    rows = []
    for m in members:
        remove_btn = ''
        if m.role != 'owner':
            remove_btn = f'<button class="zly-btn zly-btn-danger" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-delete="/api/v1/workspaces/{default_ws.id}/members/{m.user_id}" hx-target="closest tr" hx-swap="outerHTML" hx-confirm="Remove this member?">Remove</button>'
        rows.append(f'''<tr>
            <td style="font-family:Space Mono,monospace;font-size:0.75rem;">{m.user_id[:8]}...</td>
            <td><span class="zly-badge zly-badge-role">{m.role}</span></td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-muted);">{m.joined_at.strftime('%Y-%m-%d') if m.joined_at else ''}</td>
            <td style="text-align:right;white-space:nowrap;">{remove_btn}</td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="4" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO MEMBERS FOUND.</td></tr>')
    return HTMLResponse("".join(rows))


@router.get("/dashboard/invites/new-form", response_class=HTMLResponse)
async def invite_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/invite_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/sessions", response_class=HTMLResponse)
async def sessions_list(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    current_jti = None
    token = request.cookies.get("zly_token")
    if token:
        try:
            payload = decode_jwt(token)
            current_jti = payload.get("jti")
        except Exception:
            pass
    sessions = await list_sessions(current_user.id, current_jti=current_jti)
    return templates.TemplateResponse(
        request, "partials/session_rows.html",
        {"sessions": sessions},
    )


@router.get("/dashboard/bio/links/new-form", response_class=HTMLResponse)
async def bio_link_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    bio_id = ""
    if default_ws:
        bio = await get_bio_page(db, default_ws.id)
        if bio:
            bio_id = bio.id
    return templates.TemplateResponse(
        request, "partials/bio_link_form.html",
        {"bio_id": bio_id, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/links/{link_id}/variants/list", response_class=HTMLResponse)
async def variants_list(
    request: Request,
    link_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.link_service import get_link_by_id
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404)
    variants, _, _ = await list_variants(db, link_id)
    rows = []
    for v in variants:
        default_badge = '<span class="zly-badge zly-badge-active">Default</span>' if v.is_default else '<span class="zly-badge zly-badge-hidden">Variant</span>'
        rows.append(f'''<tr>
            <td style="max-width:16rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:Space Mono,monospace;font-size:0.7rem;">{h(v.destination_url)}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.7rem;">{v.weight}%</td>
            <td>{default_badge}</td>
            <td style="text-align:right;white-space:nowrap;">
                <button class="zly-btn zly-btn-secondary" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-get="/dashboard/links/{link_id}/variants/{v.id}/edit-form" hx-target="#variant-form-modal" hx-swap="innerHTML">Edit</button>
                <button class="zly-btn zly-btn-danger" style="font-size:0.55rem;padding:0.25rem 0.6rem;display:inline-flex;" hx-delete="/api/v1/links/{link_id}/variants/{v.id}" hx-target="closest tr" hx-swap="outerHTML" hx-confirm="Delete this variant?">Delete</button>
            </td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="4" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;letter-spacing:0.05em;">NO VARIANTS YET. ADD ONE TO START A/B TESTING.</td></tr>')
    return HTMLResponse("".join(rows))


@router.get("/dashboard/links/{link_id}/variants/new-form", response_class=HTMLResponse)
async def variant_new_form(
    request: Request,
    link_id: str,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request, "partials/variant_form.html",
        {"link_id": link_id},
    )


@router.get("/dashboard/links/{link_id}/variants/{variant_id}/edit-form", response_class=HTMLResponse)
async def variant_edit_form(
    request: Request,
    link_id: str,
    variant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    variant = await get_variant(db, variant_id)
    if not variant:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/variant_form.html",
        {"variant": variant, "link_id": link_id},
    )


@router.get("/dashboard/bio/links/{link_id}/edit-form", response_class=HTMLResponse)
async def bio_link_edit_form(
    request: Request,
    link_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bio_link = await get_bio_link(db, link_id)
    if not bio_link:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/bio_link_form.html",
        {"bio_link": bio_link, "workspace_id": ""},
    )


# -------- Email Campaigns HTMX --------


@router.get("/dashboard/email/contacts/list", response_class=HTMLResponse)
async def email_contacts_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="4" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    contacts, _, _ = await list_contacts(db, default_ws.id)
    from app.schemas.email_campaign import EmailContactResponse
    contact_responses = [EmailContactResponse.model_validate(c) for c in contacts]
    request.state.current_workspace_id = default_ws.id
    return templates.TemplateResponse(
        request, "partials/email_contact_rows.html",
        {"contacts": contact_responses, "workspace_id": default_ws.id},
    )


@router.get("/dashboard/email/contacts/new-form", response_class=HTMLResponse)
async def email_contact_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/email_contact_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/email/templates/list", response_class=HTMLResponse)
async def email_templates_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="5" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    templates_list, _, _ = await list_templates(db, default_ws.id)
    from app.schemas.email_campaign import EmailTemplateResponse
    template_responses = [EmailTemplateResponse.model_validate(t) for t in templates_list]
    return templates.TemplateResponse(
        request, "partials/email_template_rows.html",
        {"templates": template_responses, "workspace_id": default_ws.id},
    )


@router.get("/dashboard/email/templates/new-form", response_class=HTMLResponse)
async def email_template_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/email_template_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/email/templates/{template_id}/edit-form", response_class=HTMLResponse)
async def email_template_edit_form(
    request: Request,
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404)
    from app.schemas.email_campaign import EmailTemplateResponse
    return templates.TemplateResponse(
        request, "partials/email_template_form.html",
        {"template": EmailTemplateResponse.model_validate(template), "workspace_id": template.workspace_id},
    )


@router.get("/dashboard/email/campaigns/list", response_class=HTMLResponse)
async def email_campaigns_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<tr><td colspan="6" style="text-align:center;padding:2rem 1rem;color:var(--zly-muted);">NO WORKSPACE</td></tr>')
    campaigns, _, _ = await list_campaigns(db, default_ws.id)
    from app.schemas.email_campaign import EmailCampaignResponse
    campaign_responses = [EmailCampaignResponse.model_validate(c) for c in campaigns]
    return templates.TemplateResponse(
        request, "partials/email_campaign_rows.html",
        {"campaigns": campaign_responses, "workspace_id": default_ws.id},
    )


@router.get("/dashboard/email/campaigns/new-form", response_class=HTMLResponse)
async def email_campaign_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        request, "partials/email_campaign_form.html",
        {"workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/email/campaigns/{campaign_id}/edit-form", response_class=HTMLResponse)
async def email_campaign_edit_form(
    request: Request,
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404)
    from app.schemas.email_campaign import EmailCampaignResponse
    return templates.TemplateResponse(
        request, "partials/email_campaign_form.html",
        {"campaign": EmailCampaignResponse.model_validate(campaign), "workspace_id": campaign.workspace_id},
    )


@router.get("/dashboard/email/campaigns/{campaign_id}/stats", response_class=HTMLResponse)
async def email_campaign_stats(
    request: Request,
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404)
    stats = await update_campaign_stats(db, campaign_id)
    from app.schemas.email_campaign import EmailCampaignResponse
    return templates.TemplateResponse(
        request, "partials/email_campaign_stats.html",
        {"campaign": EmailCampaignResponse.model_validate(campaign), "stats": stats, "workspace_id": campaign.workspace_id},
    )


# -------- Admin HTML endpoints --------


@router.get("/dashboard/admin/stats", response_class=HTMLResponse)
async def admin_stats_html(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_superuser:
        return HTMLResponse('<div style="color:var(--zly-muted);padding:2rem;">Admin access required.</div>')
    from sqlalchemy import func, select
    from app.models.click import Click
    from app.models.link import Link
    from app.models.workspace import Workspace, WorkspaceMember
    from app.models.webhook import Webhook
    from app.models.email_campaign import EmailCampaign, EmailContact
    from app.models.audit import AuditLog
    users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    workspaces = (await db.execute(select(func.count()).select_from(Workspace))).scalar() or 0
    links = (await db.execute(select(func.count()).select_from(Link))).scalar() or 0
    clicks = (await db.execute(select(func.count()).select_from(Click))).scalar() or 0
    webhooks = (await db.execute(select(func.count()).select_from(Webhook))).scalar() or 0
    members = (await db.execute(select(func.count()).select_from(WorkspaceMember))).scalar() or 0
    campaigns = (await db.execute(select(func.count()).select_from(EmailCampaign))).scalar() or 0
    contacts = (await db.execute(select(func.count()).select_from(EmailContact))).scalar() or 0
    audit = (await db.execute(select(func.count()).select_from(AuditLog))).scalar() or 0
    return templates.TemplateResponse(
        request, "partials/admin_stats.html",
        {"users": users, "workspaces": workspaces, "links": links, "clicks": clicks,
         "webhooks": webhooks, "members": members, "campaigns": campaigns, "contacts": contacts, "audit": audit},
    )


@router.get("/dashboard/admin/audit-logs/list", response_class=HTMLResponse)
async def admin_audit_logs_list(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_superuser:
        return HTMLResponse('<tr><td colspan="6" style="color:var(--zly-muted);padding:2rem;">Admin access required.</td></tr>')
    from app.models.audit import AuditLog
    from sqlalchemy import select
    from app.schemas.audit import AuditLogResponse
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(50)
    )
    logs = [AuditLogResponse.model_validate(l) for l in result.scalars().all()]
    rows = []
    for log in logs:
        action_style = 'color:var(--zly-emerald);'
        if log.action in ('delete', 'revoke', 'remove'):
            action_style = 'color:#ff6b35;'
        elif log.action in ('create', 'invite', 'add'):
            action_style = 'color:#22c55e;'
        elif log.action in ('update', 'change'):
            action_style = 'color:#60a5fa;'
        rows.append(f'''<tr>
            <td><span style="font-family:Space Mono,monospace;font-size:0.65rem;{action_style}">{log.action}</span></td>
            <td style="font-family:Space Grotesk,sans-serif;font-size:0.65rem;">{log.resource_type}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.6rem;color:var(--zly-muted);">{log.resource_id[:12]}...</td>
            <td style="font-family:Space Mono,monospace;font-size:0.6rem;color:var(--zly-muted);">{log.user_id[:8]}...</td>
            <td style="font-family:Space Mono,monospace;font-size:0.6rem;color:var(--zly-muted);">{log.ip_address or '—'}</td>
            <td style="font-family:Space Mono,monospace;font-size:0.6rem;color:var(--zly-muted);">{log.created_at.strftime('%Y-%m-%d %H:%M') if log.created_at else ''}</td>
        </tr>''')
    if not rows:
        return HTMLResponse('<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--zly-muted);">No audit logs yet.</td></tr>')
    return HTMLResponse("".join(rows))


# -------- Top Links HTML --------


@router.get("/dashboard/top-links", response_class=HTMLResponse)
async def top_links_html(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces, _, _ = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    if not default_ws:
        return HTMLResponse('<div style="text-align:center;padding:2rem;color:var(--zly-muted);">NO WORKSPACE</div>')
    from app.services.link_service import get_links
    links, total, has_next = await get_links(db, default_ws.id, page=1, page_size=10)
    sorted_links = sorted(links, key=lambda l: l.clicks or 0, reverse=True)
    if not sorted_links:
        return HTMLResponse('<div style="text-align:center;padding:2rem;color:var(--zly-muted);font-family:Space Grotesk,sans-serif;font-size:0.7rem;">No links yet.</div>')
    rows = []
    for i, link in enumerate(sorted_links[:10]):
        rows.append(f'''<div style="display:flex;justify-content:space-between;align-items:center;padding:0.6rem 0;border-bottom:1px solid var(--zly-line);">
            <div style="display:flex;align-items:center;gap:0.75rem;">
                <span style="font-family:Space Mono,monospace;font-size:0.6rem;color:var(--zly-muted);width:1.2rem;">#{i+1}</span>
                <code style="font-family:Space Mono,monospace;font-size:0.7rem;color:var(--zly-emerald);">/{h(link.short_code)}</code>
            </div>
            <div style="display:flex;align-items:center;gap:1rem;">
                <span style="font-family:Space Mono,monospace;font-size:0.65rem;color:var(--zly-cream);">{link.clicks or 0} clicks</span>
                <a href="/dashboard/links/{link.id}" class="zly-btn zly-btn-secondary" style="font-size:0.55rem;padding:0.2rem 0.5rem;">View</a>
            </div>
        </div>''')
    return HTMLResponse(
        f'<div class="zly-card" style="padding:1rem;"><h3 style="font-size:0.65rem;letter-spacing:0.12em;color:var(--zly-muted);margin-bottom:0.5rem;">Top Links by Clicks</h3>{"".join(rows)}</div>'
    )
