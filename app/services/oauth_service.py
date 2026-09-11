import secrets
from urllib.parse import urlencode

import httpx

from app.config import settings


def _generate_state() -> str:
    return secrets.token_urlsafe(32)


def get_google_login_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_url,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def get_github_login_url(state: str) -> str:
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.oauth_redirect_url,
        "response_type": "code",
        "scope": "read:user user:email",
        "state": state,
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


async def exchange_google_code(code: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "redirect_uri": settings.oauth_redirect_url,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            return None
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            return None
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            return None
        return user_resp.json()


async def exchange_github_code(code: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.oauth_redirect_url,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            return None
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            return None
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        if user_resp.status_code != 200:
            return None
        data = user_resp.json()
        emails_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        primary_email = None
        if emails_resp.status_code == 200:
            for e in emails_resp.json():
                if e.get("primary"):
                    primary_email = e.get("email")
                    break
            if not primary_email and emails_resp.json():
                primary_email = emails_resp.json()[0].get("email")
        data["email"] = data.get("email") or primary_email
        return data
