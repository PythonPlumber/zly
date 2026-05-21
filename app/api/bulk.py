import csv
from io import StringIO

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.config import settings
from app.models.user import User
from app.schemas.link import BulkImportResponse
from app.services.link_service import bulk_create_links, export_links_csv
from app.services.notification_service import check_expiring_links
from app.services.workspace_service import verify_workspace_access

router = APIRouter()


@router.post("/workspaces/{workspace_id}/links/bulk-import")
async def api_bulk_import(
    workspace_id: str,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
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
    return result


@router.get("/workspaces/{workspace_id}/links/export")
async def api_export_links(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_workspace_access(db, workspace_id, current_user)
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
    await verify_workspace_access(db, workspace_id, current_user)
    result = await check_expiring_links(db, workspace_id, within_hours)
    return {"notified": len(result), "links": result}
