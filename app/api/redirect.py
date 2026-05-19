from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis_client
from app.services.link_service import get_link_by_code

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
    except ConnectionError:
        pass

    link = await get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    if not link.is_active:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link is inactive")

    try:
        await redis.set(f"link:{short_code}", link.destination_url)
    except ConnectionError:
        pass

    return Response(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"location": link.destination_url},
    )
