from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.analytics import ClickStats, WorkspaceSummary
from app.services.analytics_service import (
    get_browser_stats,
    get_clicks_over_time,
    get_device_stats,
    get_hourly_stats,
    get_os_stats,
    get_top_cities,
    get_top_countries,
    get_top_referrers,
    get_total_clicks,
    get_unique_clicks,
    get_workspace_summary,
)
from app.services.link_service import get_link_by_id
from app.services.workspace_service import verify_workspace_access

router = APIRouter(tags=["analytics"])


@router.get("/links/{link_id}/analytics", response_model=ClickStats)
async def api_link_analytics(
    link_id: str,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="analytics:view")

    return ClickStats(
        total_clicks=await get_total_clicks(db, link_id),
        clicks_over_time=await get_clicks_over_time(db, link_id, days),
        top_referrers=await get_top_referrers(db, link_id),
        browsers=await get_browser_stats(db, link_id),
        devices=await get_device_stats(db, link_id),
        oss=await get_os_stats(db, link_id),
        unique_clicks=await get_unique_clicks(db, link_id),
        top_countries=await get_top_countries(db, link_id),
        top_cities=await get_top_cities(db, link_id),
        hourly_stats=await get_hourly_stats(db, link_id),
    )


@router.get("/links/{link_id}/analytics/export")
async def api_link_analytics_export(
    link_id: str,
    format: str = "csv",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="analytics:view")
    if format == "csv":
        from io import StringIO
        import csv
        from app.models.click import Click
        from sqlalchemy import select
        result = await db.execute(select(Click).where(Click.link_id == link_id).order_by(Click.timestamp.desc()))
        clicks = result.scalars().all()
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "country", "city", "browser", "os", "device_type", "referrer_domain", "ip_hash"])
        for c in clicks:
            writer.writerow([c.timestamp, c.country or "", c.city or "", c.browser or "", c.os or "", c.device_type or "", c.referrer_domain or "", c.ip_hash or ""])
        from fastapi.responses import Response
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=analytics-{link_id}.csv"})
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported format")


@router.get("/workspaces/{workspace_id}/analytics/summary", response_model=WorkspaceSummary)
async def api_workspace_summary(
    workspace_id: str,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="analytics:view")
    return await get_workspace_summary(db, workspace_id, days)
