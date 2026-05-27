from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user_from_cookie as get_current_user
from app.models.user import User
from app.services.session_service import revoke_session
from app.core.security import decode_access_token as decode_jwt

router = APIRouter()
env = Environment(loader=FileSystemLoader("app/templates"), cache_size=0)
templates = Jinja2Templates(env=env)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@router.get("/auth/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request, "auth/forgot_password.html")


@router.get("/auth/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = ""):
    return templates.TemplateResponse(request, "auth/reset_password.html", {"token": token})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html")


@router.get("/invite/{token}", response_class=HTMLResponse)
async def invite_page(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    from app.services.invite_service import get_invite_email_data
    invite_data = await get_invite_email_data(db, token, str(request.base_url))
    if not invite_data:
        return templates.TemplateResponse(request, "errors/404.html")
    return templates.TemplateResponse(request, "auth/invite.html", {"invite": invite_data, "token": token})


@router.post("/logout")
async def logout(request: Request):
    token = request.cookies.get("zly_token")
    if token:
        try:
            payload = decode_jwt(token)
            jti = payload.get("jti")
            user_id = payload.get("sub")
            if jti and user_id:
                await revoke_session(user_id, jti)
        except Exception:
            pass
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("zly_token", path="/")
    return response
