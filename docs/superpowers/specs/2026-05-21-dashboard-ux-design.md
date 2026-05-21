# Dashboard UX Sprint — Design Spec

**Date:** 2026-05-21
**Author:** PythonPlumber
**Status:** Approved

## Overview

Zly has 66 API routes, 14 database tables, and full feature parity (short links, analytics,
QR codes, A/B testing, link-in-bio, teams, webhooks, tags, rate limiting) — but **zero
browser-based authentication flow**. Every dashboard route requires a Bearer JWT token,
making the app unusable through a web browser. This sprint adds:

1. HTTP-only cookie auth + login/register HTML pages
2. Five management dashboard pages (Domains, API Keys, Webhooks, Tags, Workspace Switcher)
3. Public bio page HTML route (linking the orphaned template)

## Design System

### Colors (Monochrome + Red)

| Role | Hex | Usage |
|------|-----|-------|
| Background | `#000000` | Page background |
| Card bg | `#1a1a1a` | Cards, inputs, sidebar |
| Card border | `#2a2a2a` | Borders |
| Text primary | `#ffffff` | Headings, body text |
| Text muted | `#888888` | Labels, secondary text |
| Red accent | `#ef4444` | Primary buttons, active links, hover states |
| Red dark | `#dc2626` | Button hover, focus rings |
| Red subtle | `rgba(239, 68, 68, 0.1)` | Badges, backgrounds |

### Typography
- **Headings:** Fredoka (same as before)
- **Body:** Inter

### UI Components
All existing `.zly-*` CSS classes in `base.html` are reused with updated CSS
custom properties. The existing sidebar layout (240px fixed, main content offset)
remains unchanged.

---

## Section 1: HTTP-Only Cookie Auth

### Cookie Details
- **Name:** `zly_token`
- **Flags:** HttpOnly, Secure (production), Path=/, SameSite=Lax
- **Max-Age:** Matches JWT expiry (`JWT_EXPIRE_MINUTES` from settings)

### Backend Changes

#### `app/core/security.py` — new dependency
```python
async def get_current_user_from_cookie(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("zly_token")
    if not token and credentials:
        token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

Priority: cookie > Bearer header > 401. This way browser users are authenticated
via cookie, while API clients continue using Bearer tokens.

#### `app/api/auth.py` — add Set-Cookie to login/register responses
Both `POST /api/v1/auth/login` and `POST /api/v1/auth/register` already return
`TokenResponse`. We wrap the response to include a `Set-Cookie` header:

```python
response = JSONResponse(content=token_data.model_dump())
response.set_cookie(
    key="zly_token",
    value=token_data.access_token,
    httponly=True,
    secure=settings.environment == "production",
    samesite="lax",
    max_age=settings.jwt_expire_minutes * 60,
    path="/",
)
return response
```

#### `app/routes/auth_routes.py` (new file) — login/register HTML pages

| Route | Method | Description |
|-------|--------|-------------|
| `/login` | GET | Render login.html template |
| `/register` | GET | Render register.html template |
| `/logout` | POST | Clear zly_token cookie, redirect to /login |

Both `login.html` and `register.html` are standalone (do NOT extend `base.html`).
They are dark-themed centered cards with:
- Zly logo at top
- Gradient red border on card
- Email + password fields
- "Log in" / "Sign up" buttons (.zly-btn-primary styled red)
- Link to switch between login/register
- Error display via HTMX response swap

The forms use HTMX to POST to `/api/v1/auth/login` and `/api/v1/auth/register`.
On success (handled via `HX-Redirect` header or `hx-redirect`), the browser
navigates to `/dashboard`. On error, the error message is swapped into the form.

#### `app/routes/dashboard.py` — switch auth dependency
All 5 existing dashboard routes change from `get_current_user` to
`get_current_user_from_cookie`. No other changes.

### Templates

#### `app/templates/auth/login.html`
Centered layout, dark bg, red-accent card:
```
┌──────────────────────────────────┐
│           ✦ Zly                  │
│                                  │
│  Email:    [______________]      │
│  Password: [______________]      │
│                                  │
│  [ 🔴 Log in ]                  │
│                                  │
│  Don't have an account? Sign up  │
└──────────────────────────────────┘
```

#### `app/templates/auth/register.html`
Same layout, adds "Confirm Password" field.

### Tests
- `tests/test_api/test_auth.py:test_login_sets_cookie` — verify Set-Cookie on login
- `tests/test_api/test_auth.py:test_register_sets_cookie` — verify Set-Cookie on register
- `tests/test_routes/test_auth_routes.py` (new):
  - `test_login_page_renders` — GET /login returns 200, HTML, contains "Log in"
  - `test_register_page_renders` — GET /register returns 200, HTML, contains "Sign up"
  - `test_logout_clears_cookie` — POST /logout clears cookie, redirects

---

## Section 2: Management Dashboard Pages

### Sidebar Changes (`base.html`)
New links added to sidebar nav, after "Bio Page", before "Settings":
```html
<a href="/dashboard/domains" class="sidebar-link">Domains</a>
<a href="/dashboard/api-keys" class="sidebar-link">API Keys</a>
<a href="/dashboard/webhooks" class="sidebar-link">Webhooks</a>
<a href="/dashboard/tags" class="sidebar-link">Tags</a>
```
Active state uses red instead of pink/purple gradient.

### New Routes in `app/routes/dashboard.py`

| Route | Template | Context |
|-------|----------|---------|
| `GET /dashboard/domains` | `dashboard/domains.html` | `user`, `workspace_id` |
| `GET /dashboard/api-keys` | `dashboard/api_keys.html` | `user`, `workspace_id` |
| `GET /dashboard/webhooks` | `dashboard/webhooks.html` | `user`, `workspace_id` |
| `GET /dashboard/tags` | `dashboard/tags.html` | `user`, `workspace_id` |

All routes use `get_current_user_from_cookie` and `get_db`. They fetch the user's
workspaces, derive `workspace_id` from default workspace, and pass to template.

### Template Pattern

Each page follows this structure:
```html
{% extends "base.html" %}
{% block title %}Page — Zly{% endblock %}
{% block content %}
<div style="max-width: 72rem; margin: 0 auto;">
  <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
    <h1 style="font-size: 1.75rem;">Page Title</h1>
    <button class="zly-btn zly-btn-primary" hx-get="..." hx-target="body">+ Add</button>
  </div>
  <div class="zly-card" style="padding: 0; overflow: hidden;">
    <table class="zly-table">
      <thead><tr><th>Name</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody id="tbody" hx-get="/api/v1/workspaces/{id}/..." hx-trigger="load"></tbody>
    </table>
  </div>
</div>
{% endblock %}
```

Each table row includes action buttons (Edit, Delete, Verify) that trigger HTMX
requests to existing API endpoints.

#### Domains Page (`app/templates/dashboard/domains.html`)
- Table: Domain, Status (Verified/Pending), Created, Actions (Verify, Delete)
- "Add Domain" button opens inline form (HTMX swap)
- Verify shows the TXT verification code in a copyable box
- Uses: `GET /api/v1/workspaces/{ws_id}/domains`, `POST .../domains`, `POST .../domains/{id}/verify`, `DELETE .../domains/{id}`

#### API Keys Page (`app/templates/dashboard/api_keys.html`)
- Table: Name, Key Prefix, Last Used, Created, Actions (Revoke)
- "Create Key" button opens form, shows raw key once after creation
- Uses: `GET .../api-keys`, `POST .../api-keys`, `DELETE .../api-keys/{id}`

#### Webhooks Page (`app/templates/dashboard/webhooks.html`)
- Table: Name, URL, Events, Status (Active/Inactive), Actions (Edit, Delete)
- "Add Webhook" opens form with URL, events checkboxes, secret field
- Uses: `GET .../webhooks`, `POST .../webhooks`, `PATCH .../webhooks/{id}`, `DELETE .../webhooks/{id}`

#### Tags Page (`app/templates/dashboard/tags.html`)
- Table: Tag Name, Color (colored dot), Links Count, Actions (Edit, Delete)
- "Create Tag" opens form with name + color picker
- Uses: `GET .../tags`, `POST .../tags`, `PATCH .../tags/{id}`, `DELETE .../tags/{id}`

### Sidebar Active State
The sidebar `active` class changes from pink/purple gradient to red:
```css
.sidebar-link.active {
    color: white;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
}
```

### Tests
- `tests/test_routes/test_dashboard_routes.py` (new):
  - `test_domains_page` — GET /dashboard/domains returns 200
  - `test_api_keys_page` — GET /dashboard/api-keys returns 200
  - `test_webhooks_page` — GET /dashboard/webhooks returns 200
  - `test_tags_page` — GET /dashboard/tags returns 200

All tests use the `auth_client` fixture (already has Bearer token).

---

## Section 3: Public Bio Page Route

### Current State
`app/templates/bio/public.html` exists (77 lines, 3 themes) but no route renders it.
The API endpoint `GET /api/v1/bio/{slug}` returns JSON only.

### Fix
Add one route to `app/routes/dashboard.py`:
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

This route does NOT use auth — bio pages are public.

### Test
- `tests/test_routes/test_public_bio.py` (new):
  - `test_public_bio_page_renders` — create bio page, GET /bio/{slug} returns 200 HTML
  - `test_public_bio_page_not_found` — GET /bio/nonexistent returns 404
  - `test_public_bio_page_unpublished` — unpublished bio returns 404

---

## Implementation Order

1. **Color system update** — Replace CSS variables in `base.html` (pink/purple/blue → red/black/white)
2. **Cookie auth dependency** — `get_current_user_from_cookie` in `security.py`
3. **Login/register API cookie setting** — Modify `auth.py` responses
4. **Auth HTML pages** — `auth_routes.py` + `login.html` + `register.html`
5. **Dashboard cookie switch** — Change dashboard routes to use cookie auth
6. **Management pages** — 4 new routes + 4 templates + sidebar update
7. **Public bio route** — One route in dashboard.py
8. **Tests** — Auth cookie tests, route rendering tests, bio page tests

## Files Changed (Summary)

| File | Action |
|------|--------|
| `app/templates/base.html` | Update CSS vars (pink/purple → red/black/white), add sidebar links |
| `app/core/security.py` | Add `get_current_user_from_cookie` dependency |
| `app/api/auth.py` | Add Set-Cookie to login/register responses |
| `app/routes/auth_routes.py` | New — login/register/logout HTML routes |
| `app/templates/auth/login.html` | New — login form |
| `app/templates/auth/register.html` | New — register form |
| `app/routes/dashboard.py` | Switch to cookie auth, add 4 management routes + bio route |
| `app/templates/dashboard/domains.html` | New — domains management |
| `app/templates/dashboard/api_keys.html` | New — API keys management |
| `app/templates/dashboard/webhooks.html` | New — webhooks management |
| `app/templates/dashboard/tags.html` | New — tags management |
| `tests/test_api/test_auth.py` | Add cookie tests |
| `tests/test_routes/test_auth_routes.py` | New — auth page rendering tests |
| `tests/test_routes/test_dashboard_routes.py` | New — management page rendering tests |
| `tests/test_routes/test_public_bio.py` | New — bio page HTML route tests |
