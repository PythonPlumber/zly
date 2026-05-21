from fastapi import APIRouter

from app.api import ab_testing, analytics, api_keys, auth, bio, domains, invites, links, redirect, workspaces

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(links.router, prefix="/links", tags=["links"])
api_router.include_router(workspaces.router)
api_router.include_router(api_keys.router)
api_router.include_router(analytics.router)
api_router.include_router(invites.router)
api_router.include_router(bio.router)
api_router.include_router(domains.router)
api_router.include_router(ab_testing.router)

redirect_router = APIRouter()
redirect_router.include_router(redirect.router, tags=["redirect"])
