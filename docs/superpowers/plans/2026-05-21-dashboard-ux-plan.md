# Dashboard UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add browser-based auth (login/register HTML pages, HTTP-only cookie), 4 management dashboard pages, and public bio page HTML route.

**Architecture:** Existing FastAPI app gets cookie auth dependency alongside Bearer token auth. Login/register API endpoints set `Set-Cookie`. 5 new Jinja2 templates (auth standalone + dashboard pages) follow monochrome+red design system. All data fetches use existing API endpoints via HTMX.

**Tech Stack:** FastAPI, Jinja2, HTMX, Tailwind CSS (CDN), PyramidJWT, bcrypt

**Design System:** Black (`#000`), dark gray cards (`#1a1a1a`), white text (`#fff`), red accent (`#ef4444`)

---

### Task 1: Update `base.html` color system to monochrome+red

**Files:**
- Modify: `app/templates/base.html`
- Verify: visual inspection after change

- [ ] **Step 1: Update CSS custom properties**

Replace the entire `:root` block (current lines 12-24) with:

```css
:root {
    --zly-red: #ef4444;
    --zly-red-dark: #dc2626;
    --zly-bg: #000000;
    --zly-card: #1a1a1a;
    --zly-card-border: #2a2a2a;
    --zly-text: #ffffff;
    --zly-muted: #888888;
}
```

- [ ] **Step 2: Update logo style**

Change `.zly-logo` and `.zly-logo-small` gradient to solid red:
```css
.zly-logo {
    font-family: 'Fredoka', sans-serif;
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--zly-red);
}
.zly-logo-small {
    font-family: 'Fredoka', sans-serif;
    font-weight: 700;
    color: var(--zly-red);
}
```

- [ ] **Step 3: Update button styles**

Replace `.zly-btn-primary`:
```css
.zly-btn-primary {
    background: var(--zly-red);
    color: white;
}
.zly-btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
}
```

Replace `.zly-btn-secondary:hover` border color:
```css
.zly-btn-secondary:hover {
    border-color: var(--zly-red);
    transform: translateY(-2px);
}
```

- [ ] **Step 4: Update input focus state**

```css
.zly-input:focus {
    border-color: var(--zly-red);
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
}
```

- [ ] **Step 5: Update sidebar hover/active states**

```css
.sidebar-link:hover {
    color: var(--zly-text);
    background: rgba(239, 68, 68, 0.08);
    transform: translateX(4px);
}
.sidebar-link.active {
    color: white;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
}
```

- [ ] **Step 6: Add new sidebar nav links**

After the Bio Page link in the sidebar nav (after line 236), add:
```html
<a href="/dashboard/domains" class="sidebar-link {% if '/dashboard/domains' in request.url.path %}active{% endif %}">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/></svg>
    Domains
</a>
<a href="/dashboard/api-keys" class="sidebar-link {% if '/dashboard/api-keys' in request.url.path %}active{% endif %}">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/></svg>
    API Keys
</a>
<a href="/dashboard/webhooks" class="sidebar-link {% if '/dashboard/webhooks' in request.url.path %}active{% endif %}">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
    Webhooks
</a>
<a href="/dashboard/tags" class="sidebar-link {% if '/dashboard/tags' in request.url.path %}active{% endif %}">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/></svg>
    Tags
</a>
```

- [ ] **Step 7: Commit**

```bash
git add app/templates/base.html
git commit -m "feat: redesign color system to monochrome+red; add sidebar nav for domains, api-keys, webhooks, tags"
```

---

### Task 2: Add cookie auth dependency + Set-Cookie on login/register

**Files:**
- Modify: `app/core/security.py`
- Modify: `app/api/auth.py`
- Test: `tests/test_api/test_auth.py`

- [ ] **Step 1: Write failing tests for cookie auth**

Add to `tests/test_api/test_auth.py`:
```python
@pytest.mark.asyncio
async def test_login_sets_cookie(client: AsyncClient, db_session: AsyncSession):
    from app.schemas.auth import RegisterRequest
    from app.services.auth_service import register_user
    await register_user(db_session, RegisterRequest(email="cookie@test.com", password="testpass123"))
    r = await client.post("/api/v1/auth/login", json={"email": "cookie@test.com", "password": "testpass123"})
    assert r.status_code == 200
    assert "zly_token" in r.cookies
    assert r.cookies["zly_token"] is not None


@pytest.mark.asyncio
async def test_register_sets_cookie(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={"email": "cookie2@test.com", "password": "testpass123"})
    assert r.status_code == 201
    assert "zly_token" in r.cookies
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api/test_auth.py::test_login_sets_cookie tests/test_api/test_auth.py::test_register_sets_cookie -v`
Expected: FAIL — cookies not set

- [ ] **Step 3: Add `get_current_user_from_cookie` to `security.py`**

Add after `get_current_user` function:

```python
from fastapi import Request


async def get_current_user_from_cookie(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("zly_token")
    if not token and credentials:
        token = credentials.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

Also add `from fastapi import Request` at the top imports.

- [ ] **Step 4: Add Set-Cookie to login and register responses**

In `app/api/auth.py`, add `from fastapi import Response` to imports and `from app.config import settings` to imports. Then update login and register to set cookie via the `Response` parameter:

Login endpoint — add `response: Response` parameter and `set_cookie`:
```python
@router.post("/login", response_model=TokenResponse)
async def api_login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    response: Response = None,
):
    user = await authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access, refresh = await create_tokens(user)
    token_data = TokenResponse(access_token=access, refresh_token=refresh)
    response.set_cookie(
        key="zly_token",
        value=token_data.access_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )
    return token_data
```

Register endpoint — add `response: Response` parameter, create tokens on register:
```python
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def api_register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    response: Response = None,
):
    try:
        user = await register_user(db, data)
        access, refresh = await create_tokens(user)
        response.set_cookie(
            key="zly_token",
            value=access,
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=settings.jwt_expire_minutes * 60,
            path="/",
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
```

Also add `from fastapi import Response` and `from app.config import settings` at the top imports in `auth.py`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_api/test_auth.py -v`
Expected: all auth tests pass (including the 2 new cookie tests)

- [ ] **Step 6: Commit**

```bash
git add app/core/security.py app/api/auth.py tests/test_api/test_auth.py
git commit -m "feat: add cookie auth dependency and Set-Cookie on login/register"
```

---

### Task 3: Create auth HTML routes and templates (login/register/logout)

**Files:**
- Create: `app/routes/auth_routes.py`
- Create: `app/templates/auth/login.html`
- Create: `app/templates/auth/register.html`
- Modify: `app/main.py` (include new router)
- Create: `tests/test_routes/test_auth_routes.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_routes/test_auth_routes.py`:
```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_page_renders(client: AsyncClient):
    r = await client.get("/login")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "Log in" in r.text or "Sign in" in r.text or "login" in r.text.lower()


@pytest.mark.asyncio
async def test_register_page_renders(client: AsyncClient):
    r = await client.get("/register")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "Sign up" in r.text or "Register" in r.text or "register" in r.text.lower()


@pytest.mark.asyncio
async def test_logout_clears_cookie(client: AsyncClient):
    r = await client.post("/logout")
    assert r.status_code == 303 or r.status_code == 302
    set_cookie = r.headers.get("set-cookie", "")
    assert "zly_token=;" in set_cookie or "Max-Age=0" in set_cookie
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_routes/test_auth_routes.py -v`
Expected: FAIL — 404 Not Found

- [ ] **Step 3: Create auth routes**

Create `app/routes/auth_routes.py`:
```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("zly_token", path="/")
    return response
```

- [ ] **Step 4: Create login template**

Create `app/templates/auth/login.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log in — Zly</title>
    <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root { --zly-red: #ef4444; --zly-red-dark: #dc2626; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: #000;
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        h1, h2, h3, h4 { font-family: 'Fredoka', 'Inter', sans-serif; font-weight: 600; }
        .auth-card {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 24px;
            padding: 2.5rem 2rem;
            width: 100%;
            max-width: 24rem;
        }
        .auth-card h1 {
            font-size: 1.5rem;
            text-align: center;
            margin-bottom: 0.25rem;
        }
        .auth-card .subtitle {
            text-align: center;
            color: #888;
            font-size: 0.875rem;
            margin-bottom: 1.5rem;
        }
        .zly-logo {
            font-family: 'Fredoka', sans-serif;
            font-weight: 700;
            font-size: 2rem;
            text-align: center;
            margin-bottom: 1.5rem;
            color: var(--zly-red);
        }
        .zly-input {
            background: #000;
            border: 1px solid #2a2a2a;
            border-radius: 10px;
            padding: 0.625rem 0.875rem;
            color: #fff;
            font-size: 0.875rem;
            width: 100%;
            outline: none;
            transition: all 0.2s ease;
        }
        .zly-input:focus { border-color: var(--zly-red); box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15); }
        .zly-input::placeholder { color: #666; }
        label { font-family: 'Fredoka', sans-serif; font-size: 0.8rem; color: #888; display: block; margin-bottom: 0.375rem; }
        .zly-btn {
            font-family: 'Fredoka', sans-serif;
            font-weight: 600;
            padding: 0.625rem 1.25rem;
            border-radius: 10px;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.9rem;
            width: 100%;
        }
        .zly-btn-primary { background: var(--zly-red); color: white; }
        .zly-btn-primary:hover { background: var(--zly-red-dark); transform: translateY(-1px); }
        .auth-link { text-align: center; margin-top: 1.25rem; font-size: 0.85rem; color: #888; }
        .auth-link a { color: var(--zly-red); text-decoration: none; font-weight: 500; }
        .auth-link a:hover { text-decoration: underline; }
        #error-msg { color: var(--zly-red); font-size: 0.8rem; text-align: center; margin-top: 0.5rem; }
        .field { margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="auth-card">
        <div class="zly-logo">✦ Zly</div>
        <h1>Welcome back</h1>
        <p class="subtitle">Log in to your account</p>
        <form hx-post="/api/v1/auth/login" hx-target="#error-msg" hx-swap="innerHTML"
              hx-redirect="/dashboard" hx-on::after-request="if(event.detail.successful) { window.location.href = '/dashboard'; }">
            <div class="field">
                <label for="email">Email</label>
                <input id="email" type="email" name="email" class="zly-input" placeholder="you@example.com" required>
            </div>
            <div class="field">
                <label for="password">Password</label>
                <input id="password" type="password" name="password" class="zly-input" placeholder="Enter your password" required>
            </div>
            <button type="submit" class="zly-btn zly-btn-primary">Log in</button>
            <div id="error-msg"></div>
        </form>
        <p class="auth-link">Don't have an account? <a href="/register">Sign up</a></p>
    </div>
</body>
</html>
```

- [ ] **Step 5: Create register template**

Create `app/templates/auth/register.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign up — Zly</title>
    <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root { --zly-red: #ef4444; --zly-red-dark: #dc2626; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: #000;
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        h1, h2, h3, h4 { font-family: 'Fredoka', 'Inter', sans-serif; font-weight: 600; }
        .auth-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 24px; padding: 2.5rem 2rem; width: 100%; max-width: 24rem; }
        .auth-card h1 { font-size: 1.5rem; text-align: center; margin-bottom: 0.25rem; }
        .auth-card .subtitle { text-align: center; color: #888; font-size: 0.875rem; margin-bottom: 1.5rem; }
        .zly-logo { font-family: 'Fredoka', sans-serif; font-weight: 700; font-size: 2rem; text-align: center; margin-bottom: 1.5rem; color: var(--zly-red); }
        .zly-input { background: #000; border: 1px solid #2a2a2a; border-radius: 10px; padding: 0.625rem 0.875rem; color: #fff; font-size: 0.875rem; width: 100%; outline: none; transition: all 0.2s ease; }
        .zly-input:focus { border-color: var(--zly-red); box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15); }
        .zly-input::placeholder { color: #666; }
        label { font-family: 'Fredoka', sans-serif; font-size: 0.8rem; color: #888; display: block; margin-bottom: 0.375rem; }
        .zly-btn { font-family: 'Fredoka', sans-serif; font-weight: 600; padding: 0.625rem 1.25rem; border-radius: 10px; border: none; cursor: pointer; transition: all 0.2s ease; font-size: 0.9rem; width: 100%; }
        .zly-btn-primary { background: var(--zly-red); color: white; }
        .zly-btn-primary:hover { background: var(--zly-red-dark); transform: translateY(-1px); }
        .auth-link { text-align: center; margin-top: 1.25rem; font-size: 0.85rem; color: #888; }
        .auth-link a { color: var(--zly-red); text-decoration: none; font-weight: 500; }
        .auth-link a:hover { text-decoration: underline; }
        #error-msg { color: var(--zly-red); font-size: 0.8rem; text-align: center; margin-top: 0.5rem; }
        .field { margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="auth-card">
        <div class="zly-logo">✦ Zly</div>
        <h1>Create account</h1>
        <p class="subtitle">Join Zly for free</p>
        <form hx-post="/api/v1/auth/register" hx-target="#error-msg" hx-swap="innerHTML"
              hx-on::after-request="if(event.detail.successful) { window.location.href = '/dashboard'; }">
            <div class="field">
                <label for="email">Email</label>
                <input id="email" type="email" name="email" class="zly-input" placeholder="you@example.com" required>
            </div>
            <div class="field">
                <label for="password">Password</label>
                <input id="password" type="password" name="password" class="zly-input" placeholder="Min. 8 characters" required minlength="8">
            </div>
            <button type="submit" class="zly-btn zly-btn-primary">Sign up</button>
            <div id="error-msg"></div>
        </form>
        <p class="auth-link">Already have an account? <a href="/login">Log in</a></p>
    </div>
</body>
</html>
```

- [ ] **Step 6: Include auth router in `app/main.py`**

Add after the import section and before other includes:
```python
from app.routes.auth_routes import router as auth_router
```
And add after the lifespan block (before `app.include_router(dashboard_router)`):
```python
app.include_router(auth_router)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest tests/test_routes/test_auth_routes.py -v`
Expected: PASS (login page renders, register page renders, logout clears cookie)

- [ ] **Step 8: Commit**

```bash
git add app/routes/auth_routes.py app/templates/auth/ app/main.py tests/test_routes/test_auth_routes.py
git commit -m "feat: add login/register HTML pages with cookie auth"
```

---

### Task 4: Switch dashboard routes to use cookie auth

**Files:**
- Modify: `app/routes/dashboard.py`
- Verify: no test changes needed (tests use auth_client which sets Bearer header, still works)

- [ ] **Step 1: Change import in dashboard.py**

Replace:
```python
from app.core.security import get_current_user
```
With:
```python
from app.core.security import get_current_user_from_cookie as get_current_user
```

This alias means all route definitions stay the same — they still reference `get_current_user`, but it now resolves to the cookie-aware version.

- [ ] **Step 2: Run existing tests to verify nothing broke**

Run: `python -m pytest tests/ -x -v`
Expected: all tests pass (auth_client uses Bearer token, which cookie dependency falls back to)

- [ ] **Step 3: Commit**

```bash
git add app/routes/dashboard.py
git commit -m "feat: switch dashboard routes to cookie-auth dependency"
```

---

### Task 5: Create management dashboard pages (Domains, API Keys, Webhooks, Tags)

**Files:**
- Modify: `app/routes/dashboard.py`
- Create: `app/templates/dashboard/domains.html`
- Create: `app/templates/dashboard/api_keys.html`
- Create: `app/templates/dashboard/webhooks.html`
- Create: `app/templates/dashboard/tags.html`
- Create: `tests/test_routes/test_dashboard_routes.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_routes/test_dashboard_routes.py`:
```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_domains_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/domains")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_api_keys_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/api-keys")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_webhooks_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/webhooks")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_tags_page(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard/tags")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_dashboard_page_works(auth_client: AsyncClient):
    r = await auth_client.get("/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_routes/test_dashboard_routes.py -v`
Expected: FAIL — 404 Not Found for domains, api-keys, webhooks, tags

- [ ] **Step 3: Add routes to dashboard.py**

Add 4 new route handlers to `app/routes/dashboard.py`:

```python
@router.get("/dashboard/domains", response_class=HTMLResponse)
async def domains_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        "dashboard/domains.html",
        {"request": request, "user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/api-keys", response_class=HTMLResponse)
async def api_keys_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        "dashboard/api_keys.html",
        {"request": request, "user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/webhooks", response_class=HTMLResponse)
async def webhooks_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        "dashboard/webhooks.html",
        {"request": request, "user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )


@router.get("/dashboard/tags", response_class=HTMLResponse)
async def tags_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await get_workspaces_for_user(db, current_user.id)
    default_ws = workspaces[0] if workspaces else None
    return templates.TemplateResponse(
        "dashboard/tags.html",
        {"request": request, "user": current_user, "workspace_id": default_ws.id if default_ws else ""},
    )
```

- [ ] **Step 4: Create domains.html template**

Create `app/templates/dashboard/domains.html`:
```html
{% extends "base.html" %}
{% block title %}Domains — Zly{% endblock %}
{% block content %}
<div style="max-width: 72rem; margin: 0 auto;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.75rem;">Custom Domains</h1>
        <button class="zly-btn zly-btn-primary" hx-get="/dashboard/domains/new-form" hx-target="#domain-form" hx-swap="innerHTML">+ Add Domain</button>
    </div>
    <div id="domain-form"></div>
    <div class="zly-card" style="padding: 0; overflow: hidden;">
        <table class="zly-table">
            <thead>
                <tr>
                    <th>Domain</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th style="text-align: right;">Actions</th>
                </tr>
            </thead>
            <tbody id="domains-tbody" hx-get="/api/v1/workspaces/{{ workspace_id }}/domains" hx-trigger="load" hx-swap="innerHTML">
                <tr><td colspan="4" style="text-align: center; padding: 2rem 1rem; color: var(--zly-muted);">Loading domains...</td></tr>
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Create api_keys.html template**

Create `app/templates/dashboard/api_keys.html`:
```html
{% extends "base.html" %}
{% block title %}API Keys — Zly{% endblock %}
{% block content %}
<div style="max-width: 72rem; margin: 0 auto;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.75rem;">API Keys</h1>
        <button class="zly-btn zly-btn-primary" hx-get="/dashboard/api-keys/new-form" hx-target="#key-form" hx-swap="innerHTML">+ Create Key</button>
    </div>
    <div id="key-form"></div>
    <div class="zly-card" style="padding: 0; overflow: hidden;">
        <table class="zly-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Key</th>
                    <th>Last Used</th>
                    <th>Created</th>
                    <th style="text-align: right;">Actions</th>
                </tr>
            </thead>
            <tbody id="keys-tbody" hx-get="/api/v1/workspaces/{{ workspace_id }}/api-keys" hx-trigger="load" hx-swap="innerHTML">
                <tr><td colspan="5" style="text-align: center; padding: 2rem 1rem; color: var(--zly-muted);">Loading API keys...</td></tr>
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 6: Create webhooks.html template**

Create `app/templates/dashboard/webhooks.html`:
```html
{% extends "base.html" %}
{% block title %}Webhooks — Zly{% endblock %}
{% block content %}
<div style="max-width: 72rem; margin: 0 auto;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.75rem;">Webhooks</h1>
        <button class="zly-btn zly-btn-primary" hx-get="/dashboard/webhooks/new-form" hx-target="#webhook-form" hx-swap="innerHTML">+ Add Webhook</button>
    </div>
    <div id="webhook-form"></div>
    <div class="zly-card" style="padding: 0; overflow: hidden;">
        <table class="zly-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>URL</th>
                    <th>Events</th>
                    <th>Active</th>
                    <th style="text-align: right;">Actions</th>
                </tr>
            </thead>
            <tbody id="webhooks-tbody" hx-get="/api/v1/workspaces/{{ workspace_id }}/webhooks" hx-trigger="load" hx-swap="innerHTML">
                <tr><td colspan="5" style="text-align: center; padding: 2rem 1rem; color: var(--zly-muted);">Loading webhooks...</td></tr>
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 7: Create tags.html template**

Create `app/templates/dashboard/tags.html`:
```html
{% extends "base.html" %}
{% block title %}Tags — Zly{% endblock %}
{% block content %}
<div style="max-width: 72rem; margin: 0 auto;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.75rem;">Tags</h1>
        <button class="zly-btn zly-btn-primary" hx-get="/dashboard/tags/new-form" hx-target="#tag-form" hx-swap="innerHTML">+ Create Tag</button>
    </div>
    <div id="tag-form"></div>
    <div class="zly-card" style="padding: 0; overflow: hidden;">
        <table class="zly-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Color</th>
                    <th>Created</th>
                    <th style="text-align: right;">Actions</th>
                </tr>
            </thead>
            <tbody id="tags-tbody" hx-get="/api/v1/workspaces/{{ workspace_id }}/tags" hx-trigger="load" hx-swap="innerHTML">
                <tr><td colspan="4" style="text-align: center; padding: 2rem 1rem; color: var(--zly-muted);">Loading tags...</td></tr>
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python -m pytest tests/test_routes/test_dashboard_routes.py -v`
Expected: PASS (all 5 pages render HTML)

- [ ] **Step 9: Commit**

```bash
git add app/routes/dashboard.py app/templates/dashboard/domains.html app/templates/dashboard/api_keys.html app/templates/dashboard/webhooks.html app/templates/dashboard/tags.html tests/test_routes/test_dashboard_routes.py
git commit -m "feat: add management dashboard pages for domains, api-keys, webhooks, tags"
```

---

### Task 6: Add public bio page HTML route

**Files:**
- Modify: `app/routes/dashboard.py`
- Create: `tests/test_routes/test_public_bio.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_routes/test_public_bio.py`:
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.bio import BioPageCreate, BioLinkCreate
from app.services.bio_service import create_bio_page, add_bio_link


@pytest.mark.asyncio
async def test_public_bio_page_renders(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    bio = await create_bio_page(
        db_session, test_workspace_id,
        BioPageCreate(slug="test-bio", title="Test Bio Page"),
    )
    await add_bio_link(
        db_session, bio.id,
        BioLinkCreate(title="My Link", url="https://example.com"),
    )
    r = await client.get("/bio/test-bio")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "Test Bio Page" in r.text


@pytest.mark.asyncio
async def test_public_bio_page_not_found(client: AsyncClient):
    r = await client.get("/bio/nonexistent-slug")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_public_bio_page_unpublished(client: AsyncClient, db_session: AsyncSession, test_workspace_id: str):
    from app.schemas.bio import BioPageCreate
    from app.services.bio_service import create_bio_page
    bio = await create_bio_page(
        db_session, test_workspace_id,
        BioPageCreate(slug="unpub-bio", title="Unpublished", is_published=False),
    )
    r = await client.get("/bio/unpub-bio")
    assert r.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_routes/test_public_bio.py -v`
Expected: FAIL — 404 Not Found for /bio/test-bio

- [ ] **Step 3: Add bio route to dashboard.py**

Add after the existing routes in `app/routes/dashboard.py`:

```python
@router.get("/bio/{slug}", response_class=HTMLResponse)
async def public_bio_page(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    from app.services.bio_service import get_bio_page_by_slug
    bio = await get_bio_page_by_slug(db, slug)
    if not bio or not bio.is_published:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "bio/public.html",
        {"request": request, "bio": bio},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_routes/test_public_bio.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/routes/dashboard.py tests/test_routes/test_public_bio.py
git commit -m "feat: add public bio page HTML route (fix orphaned template)"
```

---

### Task 7: Final verification — run full test suite

- [ ] **Step 1: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: all tests pass

- [ ] **Step 2: Check total test count**

Expected count should be approx 129 + 2 (cookie) + 3 (auth routes) + 5 (dashboard routes) + 3 (public bio) = 142 tests

- [ ] **Step 3: Commit final state**

```bash
git add -A
git commit -m "chore: final verification — all tests pass"
```
