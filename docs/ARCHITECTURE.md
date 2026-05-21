# Architecture — Zly

## Overview

Zly is a multi-tenant URL shortener built on FastAPI with async SQLAlchemy, PostgreSQL, and Redis. The system follows a service-oriented architecture with clear separation between API, business logic, and data access layers.

## Data Model

### Core Entities

```
User (1) ──── (N) WorkspaceMember ──── (N) Workspace (1)
  │                                            │
  │                                            ├── (N) Link ──── (N) Click
  │                                            │       │
  │                                            │       ├── (N) ABVariant
  │                                            │       └── (1) QR Code (generated on demand)
  │                                            │
  │                                            ├── (1) BioPage ──── (N) BioLink
  │                                            │
  │                                            ├── (N) CustomDomain
  │                                            │
  │                                            └── (N) ApiKey
  │
  └── (N) Invite
```

### Users & Authentication

- `User` — email + bcrypt-hashed password
- JWT-based auth with access/refresh token flow
- `get_current_user` dependency extracts user from Bearer token via `HTTPBearer`
- Default personal workspace auto-created on registration

### Multi-Tenancy via Workspaces

- Every resource belongs to a workspace
- `Workspace.owner_id` identifies the owner
- `WorkspaceMember` grants member-level access to additional users
- `verify_workspace_access(db, workspace_id, user, require_owner=False)` is the single authorization entry point
- Owner-only operations: workspace delete/update, invites, API keys, domains

### Links

| Column | Type | Purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `workspace_id` | UUID FK | Tenant isolation |
| `short_code` | String(10) | Unique redirect key |
| `destination_url` | Text | Redirect target |
| `title` | String | Display name |
| `password_hash` | String | Optional password protection |
| `activate_at` | DateTime | Scheduled activation (404 before) |
| `expires_at` | DateTime | Scheduled expiry (410 after) |
| `is_active` | Boolean | Manual toggle |

### Clicks

Every redirect records a `Click` with:
- `link_id`, `workspace_id` — ownership
- `timestamp` — when the click happened
- `ip_address`, `user_agent` — raw request metadata
- `referer` — HTTP Referer header
- `country`, `city`, `region` — GeoIP (reserved for future)
- `browser`, `os`, `device` — parsed from User-Agent
- `variant_id` — ABVariant selected (nullable)

### A/B Testing

- `ABVariant` per link with `weight` (integer, higher = more traffic)
- `select_variant()` uses cumulative weight distribution for weighted random selection
- Selected `variant_id` stored on `Click` for per-variant analytics

### Bio Pages

- `BioPage` — one per workspace, slug-based public URL
- `BioLink` — ordered link entries with title, URL, active toggle
- Three themes: midnight, dark, light

### Custom Domains

- `CustomDomain` — domain name + verification code (uuid4) + verified flag
- DNS TXT verification: `zly-verify=<verification_code>`
- `get_workspace_by_domain()` resolves domain to workspace for CNAME-based routing

## Routing Flow

```
Client
  │
  ├── GET /{short_code}
  │     │
  │     ├── Check Redis cache ── hit ──► 307 redirect
  │     │
  │     └── Miss:
  │           ├── Query DB for link by short_code
  │           ├── Check activate_at (404 if not yet active)
  │           ├── Check expires_at (410 if expired)
  │           ├── Check password_hash:
  │           │     ├── No password → proceed
  │           │     ├── Has password + ?password= in query → verify
  │           │     └── Has password + no query → return 401 (password required)
  │           ├── Select A/B variant (if variants exist):
  │           │     └── select_variant(link.id) → selected variant
  │           ├── Record Click (async via DB):
  │           │     ├── Parse User-Agent → browser, os, device
  │           │     ├── Store variant_id (if applicable)
  │           │     └── Store referer, IP, timestamp
  │           ├── Cache result in Redis (if available)
  │           └── 307 redirect to destination
  │
  ├── GET /dashboard/* — HTML pages (HTMX-enhanced)
  │
  ├── GET /bio/{slug} — Public bio page
  │
  └── /api/v1/* — REST API (JSON)
```

### Caching Strategy

- Redirect lookups cached in Redis: `link:{short_code}` → `{destination, password_hash, etc}`
- TTL: 1 hour (configurable in future)
- Cache invalidation: on link update/delete (future: Redis pub/sub or cache-busting)
- Graceful degradation: Redis failure falls through to DB query

## Auth Flow

```
Register ──► POST /api/v1/auth/register
  │
  ├── Hash password (bcrypt)
  ├── Create User
  ├── Create default personal workspace
  └── Return access_token + refresh_token

Login ──► POST /api/v1/auth/login
  │
  ├── Verify email + password
  └── Return access_token + refresh_token

Request ──► Any protected endpoint
  │
  ├── get_current_user dependency:
  │     ├── Extract Bearer token from Authorization header
  │     ├── Decode JWT (verify signature + expiry)
  │     ├── Fetch user from DB
  │     └── Return User or 401
  │
  └── verify_workspace_access dependency:
        ├── Check workspace.owner_id == user.id
        ├── Fallback: WorkspaceMember exists for user
        ├── require_owner=True restricts to owner only
        └── Return workspace or 403
```

## Async Patterns

### Current (Synchronous Click Recording)

Click recording happens synchronously in the redirect handler within the same DB transaction. This keeps the architecture simple for self-hosted deployments and avoids session lifecycle issues with BackgroundTasks.

### Future (arq Queue)

For high-traffic deployments, click recording will move to arq workers:

```python
# Worker (worker/main.py)
class WorkerSettings:
    functions = [record_click]

# Enqueue
await ctx['redis'].enqueue_job('record_click', click_data)
```

## Analytics Aggregation

All analytics queries aggregate from the `clicks` table:

- **Clicks Over Time**: `GROUP BY date(timestamp)` with date range filtering
- **Top Referrers**: `GROUP BY referer` (extracted domain), sorted by count DESC
- **Browsers**: `GROUP BY browser` from parsed User-Agent
- **OS/Devices**: Same pattern as browsers
- **Workspace Summary**: Aggregate across all links in a workspace, with total clicks + per-link breakdown

## Migration Strategy

- Alembic with async SQLAlchemy support
- Migrations auto-generated via `alembic revision --autogenerate`
- Test-friendly: SQLite for offline dev, PostgreSQL in production
- Initial migration captures all 10 tables
- Migrations run idempotently in CI and deployment

## Frontend Architecture

- **Templating**: Jinja2 server-side rendering
- **Interactivity**: HTMX for partial page updates (no JS build step)
- **Charts**: Chart.js loaded from CDN
- **Styling**: Tailwind CSS v4 via CDN + custom toon/editorial CSS
- **Design**: Fredoka font, gradient elements, rounded/bubbly cards, cartoon-style icons
- **No SPA**: Everything is server-rendered with progressive enhancement

## Security Considerations

| Concern | Mitigation |
|---|---|
| Password storage | bcrypt with work factor 12 |
| JWT tokens | HS256 with configurable expiry (30 min access, 7 day refresh) |
| SQL injection | SQLAlchemy parameterized queries |
| XSS | Jinja2 auto-escapes HTML |
| CSRF | HTMX uses same-origin, API uses Bearer tokens |
| Rate limiting | Future: Caddy middleware |
| Secret management | Environment variables, never committed |
| CORS | Configurable origins, restrict in production |
