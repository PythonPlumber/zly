from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.services.short_code import generate_short_code


async def create_workspace(db: AsyncSession, data: WorkspaceCreate, owner_id: str) -> Workspace:
    slug = data.slug or generate_short_code(length=8).lower()
    ws = Workspace(name=data.name, slug=slug, owner_id=owner_id)
    db.add(ws)
    await db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=owner_id, role="owner"))
    await db.flush()
    await db.refresh(ws)
    return ws


async def get_workspace(db: AsyncSession, workspace_id: str) -> Workspace | None:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def get_workspaces_for_user(db: AsyncSession, user_id: str) -> list[Workspace]:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.created_at.desc())
    )
    return list(result.scalars().all())


async def update_workspace(db: AsyncSession, ws: Workspace, data: WorkspaceUpdate) -> Workspace:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ws, field, value)
    await db.flush()
    await db.refresh(ws)
    return ws


async def delete_workspace(db: AsyncSession, ws: Workspace) -> None:
    await db.delete(ws)
    await db.flush()


async def verify_workspace_access(
    db: AsyncSession, workspace_id: str, user: User, require_owner: bool = False
) -> Workspace:
    ws = await get_workspace(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if ws.owner_id == user.id:
        return ws
    if require_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not workspace owner")
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")
    return ws
