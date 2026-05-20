from fastapi import APIRouter

from app.api import analytics, api_keys, auth, invites, links, redirect, workspaces

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(links.router, prefix="/links", tags=["links"])
api_router.include_router(workspaces.router)
api_router.include_router(api_keys.router)
api_router.include_router(analytics.router)
api_router.include_router(invites.router)

redirect_router = APIRouter()
redirect_router.include_router(redirect.router, tags=["redirect"])
