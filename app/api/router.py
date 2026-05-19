from fastapi import APIRouter

from app.api import auth, links, redirect, workspaces

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(links.router, prefix="/links", tags=["links"])
api_router.include_router(workspaces.router)

redirect_router = APIRouter()
redirect_router.include_router(redirect.router, tags=["redirect"])
