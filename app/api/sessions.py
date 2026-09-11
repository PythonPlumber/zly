from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.session_service import list_sessions, revoke_session, revoke_all_sessions

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
async def api_list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    all_sessions = await list_sessions(current_user.id)
    total = len(all_sessions)
    offset = (page - 1) * page_size
    items = all_sessions[offset:offset + page_size]
    has_next = (offset + page_size) < total
    return {"sessions": items, "total": total, "page": page, "page_size": page_size, "has_next": has_next}


@router.delete("/{jti}", status_code=status.HTTP_204_NO_CONTENT)
async def api_revoke_session(
    jti: str,
    current_user: User = Depends(get_current_user),
):
    ok = await revoke_session(current_user.id, jti)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")


@router.post("/revoke-all", status_code=status.HTTP_200_OK)
async def api_revoke_all_sessions(
    current_user: User = Depends(get_current_user),
):
    count = await revoke_all_sessions(current_user.id)
    return {"revoked": count}
