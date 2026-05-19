from fastapi import APIRouter

from app.api import links, redirect

api_router = APIRouter()
api_router.include_router(links.router, prefix="/links", tags=["links"])

redirect_router = APIRouter()
redirect_router.include_router(redirect.router, tags=["redirect"])
