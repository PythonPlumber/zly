import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session_factory
from app.models.user import User


async def _make_superuser(email: str) -> bool:
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User with email '{email}' not found")
            return False
        if user.is_superuser:
            print(f"User '{email}' is already a superuser")
            return True
        user.is_superuser = True
        await session.commit()
        print(f"User '{email}' ({user.display_name or user.email}) is now a superuser")
        return True


async def _list_superusers() -> None:
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(User).where(User.is_superuser == True).order_by(User.created_at)
        )
        users = result.scalars().all()
        if not users:
            print("No superusers found")
            return
        print(f"{'Email':<40} {'Name':<25} {'Created':<25}")
        print("-" * 90)
        for u in users:
            print(f"{u.email:<40} {(u.display_name or ''):<25} {str(u.created_at):<25}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: zly-cli makesuperuser <email>")
        print("       zly-cli list-superusers")
        sys.exit(1)

    command = sys.argv[1]
    if command == "makesuperuser":
        if len(sys.argv) < 3:
            print("Usage: zly-cli makesuperuser <email>")
            sys.exit(1)
        success = asyncio.run(_make_superuser(sys.argv[2]))
        sys.exit(0 if success else 1)
    elif command == "list-superusers":
        asyncio.run(_list_superusers())
    else:
        print(f"Unknown command: {command}")
        print("Available: makesuperuser, list-superusers")
        sys.exit(1)


if __name__ == "__main__":
    main()
