from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.folder import Folder


async def create_folder(db: AsyncSession, workspace_id: str, name: str) -> Folder:
    folder = Folder(workspace_id=workspace_id, name=name.strip())
    db.add(folder)
    await db.flush()
    await db.refresh(folder)
    return folder


async def get_folders(db: AsyncSession, workspace_id: str) -> list[Folder]:
    result = await db.execute(select(Folder).where(Folder.workspace_id == workspace_id).order_by(Folder.created_at.desc()))
    return list(result.scalars().all())


async def get_folder(db: AsyncSession, folder_id: str) -> Folder | None:
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    return result.scalar_one_or_none()


async def delete_folder(db: AsyncSession, folder: Folder) -> None:
    await db.delete(folder)
    await db.flush()
