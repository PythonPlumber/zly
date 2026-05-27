from fastapi import APIRouter

from app.api import ab_testing, admin, analytics, api_keys, audit_logs, auth, bio, bulk, domains, email_campaigns, invites, links, oauth, redirect, sessions, tags, users, webhooks, workspaces

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
api_router.include_router(webhooks.router)
api_router.include_router(bulk.router)
api_router.include_router(tags.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(audit_logs.router)
api_router.include_router(oauth.router)
api_router.include_router(email_campaigns.router)
api_router.include_router(sessions.router)

redirect_router = APIRouter()
redirect_router.include_router(redirect.router, tags=["redirect"])
