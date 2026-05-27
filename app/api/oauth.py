from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
)
from app.core.logging import get_logger
from app.models.user import User
from app.services.oauth_service import (
    _generate_state,
    exchange_github_code,
    exchange_google_code,
    get_github_login_url,
    get_google_login_url,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

_STATE_STORE: dict[str, str] = {}


@router.get("/google/login")
async def google_login():
    state = _generate_state()
    _STATE_STORE[state] = "google"
    url = get_google_login_url(state)
    return {"url": url}


@router.get("/github/login")
async def github_login():
    state = _generate_state()
    _STATE_STORE[state] = "github"
    url = get_github_login_url(state)
    return {"url": url}


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    provider = _STATE_STORE.pop(state, None)
    if not provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state parameter")

    provider = provider.lower()
    user_data = None
    if provider == "google":
        user_data = await exchange_google_code(code)
        if not user_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to authenticate with Google")
        oauth_id = user_data.get("id")
        email = user_data.get("email", "")
        display_name = user_data.get("name", "")
        avatar_url = user_data.get("picture", "")
    elif provider == "github":
        user_data = await exchange_github_code(code)
        if not user_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to authenticate with GitHub")
        oauth_id = str(user_data.get("id", ""))
        email = user_data.get("email", "")
        display_name = user_data.get("name") or user_data.get("login", "")
        avatar_url = user_data.get("avatar_url", "")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown OAuth provider")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required from OAuth provider")

    result = await db.execute(
        select(User).where(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            existing.oauth_provider = provider
            existing.oauth_id = oauth_id
            if avatar_url:
                existing.avatar_url = avatar_url
            user = existing
        else:
            user = User(
                email=email,
                oauth_provider=provider,
                oauth_id=oauth_id,
                display_name=display_name,
                avatar_url=avatar_url,
            )
            db.add(user)
            from app.models.workspace import Workspace, WorkspaceMember
            slug = email.split("@")[0]
            ws = Workspace(
                name=f"{display_name or slug}'s Workspace",
                slug=slug,
                owner_id=user.id,
            )
            db.add(ws)
            await db.flush()
            ws.owner_id = user.id
            db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="owner"))
        await db.flush()
        await db.refresh(user)

    access = create_access_token({"sub": user.id})
    refresh = create_refresh_token({"sub": user.id}, token_version=user.token_version)

    redirect_html = f"""
    <html><body>
    <script>
        localStorage.setItem("zly_access_token", "{access}");
        window.location.href = "/dashboard";
    </script>
    </body></html>
    """
    response = Response(content=redirect_html, media_type="text/html")
    response.set_cookie(
        key="zly_token",
        value=access,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400 * 7,
    )
    return response
