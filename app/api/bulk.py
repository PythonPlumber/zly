import csv
from io import StringIO

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.config import settings
from app.models.user import User
from app.services.audit_service import log_audit_event
from app.schemas.link import BulkImportResponse
from app.services.link_service import bulk_create_links, export_links_csv
from app.services.notification_service import check_expiring_links
from app.services.workspace_service import verify_workspace_access

router = APIRouter()


@router.post("/workspaces/{workspace_id}/links/bulk-import")
async def api_bulk_import(
    workspace_id: str,
    file: UploadFile,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="links:create")
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Maximum is {settings.max_upload_size_mb}MB.",
        )
    reader = csv.DictReader(StringIO(content.decode()))
    rows = list(reader)
    result = await bulk_create_links(db, rows, workspace_id, current_user.id)
    await log_audit_event(
        db,
        action="create",
        resource_type="link",
        resource_id=None,
        workspace_id=workspace_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/workspaces/{workspace_id}/links/export")
async def api_export_links(
    workspace_id: str,
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="analytics:view")
    if format == "json":
        from app.services.link_service import get_links
        links, total, has_next = await get_links(db, workspace_id, page=1, page_size=10000)
        return JSONResponse(content={"links": [{"short_code": l.short_code, "destination_url": l.destination_url, "title": l.title, "is_active": l.is_active, "expires_at": str(l.expires_at) if l.expires_at else None, "created_at": str(l.created_at) if l.created_at else None} for l in links]})
    csv_content = await export_links_csv(db, workspace_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=zly-links-{workspace_id}.csv"},
    )


@router.post("/workspaces/{workspace_id}/links/check-expiring")
async def api_check_expiring(
    workspace_id: str,
    within_hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user, required_permission="links:create")
    result = await check_expiring_links(db, workspace_id, within_hours)
    return {"notified": len(result), "links": result}
