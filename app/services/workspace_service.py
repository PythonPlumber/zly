from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
