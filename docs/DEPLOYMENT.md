# Deployment Guide — Zly

Zly can be deployed anywhere. This guide covers every option, ranked from most to least recommended.

---

## 🥇 VPS / Dedicated Server (Recommended)

Full control. Persistent PostgreSQL, Redis caching, auto-HTTPS via Caddy, zero platform lock-in.

### Prerequisites

- Linux VPS (Ubuntu 24.04+ or Debian 12+, **$5–10/mo** on [Hetzner](https://hetzner.com), [DigitalOcean](https://digitalocean.com), or [Linode](https://linode.com))
- Docker Engine 24+ and Docker Compose v2
- A domain name pointing to your server (e.g. `zly.example.com`)

### Quick Deploy

```bash
# SSH into your server
ssh root@your-server-ip

# Install Docker (Ubuntu)
apt update && apt install -y docker.io docker-compose-v2

# Clone
git clone https://github.com/pythonplumber/zly.git
cd zly

# Configure
cp infrastructure/.env.example .env
nano .env   # Set secrets, domain, etc.

# Start all services
docker compose -f infrastructure/docker-compose.yml up -d

# Run migrations
docker compose exec fastapi alembic upgrade head
```

### Environment Variables (`.env`)

```env
DATABASE_URL=postgresql+asyncpg://zly:your-password@postgres:5432/zly
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<openssl rand -hex 64>
JWT_SECRET=<openssl rand -hex 64>
CORS_ORIGINS=https://zly.example.com
DEFAULT_DOMAIN=zly.example.com
ENVIRONMENT=production
```

### What You Get

| Service | Role |
|---|---|
| **Caddy** | Reverse proxy, auto-Let's Encrypt TLS, rate limiting |
| **FastAPI** | Zly application server (4 workers) |
| **PostgreSQL** | Primary database (persistent volume) |
| **Redis** | Cache + optional job queue (persistent volume) |

### Managing

```bash
# Logs
docker compose logs -f fastapi

# Backups
docker compose exec postgres pg_dump -U zly zly > backup.sql

# Upgrades
git pull
docker compose up -d --build
docker compose exec fastapi alembic upgrade head
```

### Security

- Generate secrets with `openssl rand -hex 64`
- Set `CORS_ORIGINS` to your exact domain
- Never commit `.env` to Git

---

## 🥈 Railway

Native Docker support with a free PostgreSQL add-on and Redis. Best PaaS option.

### Steps

1. Push your repo to GitHub
2. Go to [Railway](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Add these environment variables in Railway dashboard:

```env
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>:<port>/<db>
SECRET_KEY=<random-64-char>
JWT_SECRET=<random-64-char>
CORS_ORIGINS=https://your-app.railway.app
DEFAULT_DOMAIN=your-app.railway.app
ENVIRONMENT=production
```

4. Add a **PostgreSQL** plugin — Railway auto-generates `DATABASE_URL` from it
5. Add a **Redis** plugin (optional, for caching)
6. In **Settings**, set the start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

7. Run migrations in the Railway shell:

```bash
alembic upgrade head
```

### Notes

- Railway handles HTTPS automatically
- The `$PORT` variable is auto-set by Railway
- Custom domains work via Railway's domain settings

---

## 🥉 Render

Web Service + managed PostgreSQL via Neon. No Redis (app degrades gracefully).

### Steps

1. Push your repo to GitHub
2. Go to [Render](https://render.com) → **New Web Service** → connect your repo
3. Fill in:

| Field | Value |
|---|---|
| Name | `zly` |
| Runtime | **Python 3** |
| Build Command | `pip install -e ".[dev]"` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Plan | **Starter** ($7/mo) or Free |

4. Add environment variables:

```env
DATABASE_URL=postgresql+asyncpg://<neon-user>:<pass>@<neon-host>/<db>?sslmode=require
SECRET_KEY=<random-64-char>
JWT_SECRET=<random-64-char>
CORS_ORIGINS=https://zly.onrender.com
DEFAULT_DOMAIN=zly.onrender.com
ENVIRONMENT=production
```

5. Create a **Neon** (free) or **Render PostgreSQL** database and set `DATABASE_URL`
6. Deploy, then run migrations in Render Shell:

```bash
alembic upgrade head
```

### Notes

- Free tier spins down after inactivity (slow first request)
- Upgrade to Starter for always-on
- Redis is not available on Render free tier — Zly works fine without it
- Custom domains via Render dashboard

---

## 🏅 Vercel

Serverless functions. Requires Neon/Supabase for database. No Redis.

### Prerequisites

- [Vercel account](https://vercel.com)
- [Neon](https://neon.tech) (free serverless PostgreSQL) or [Supabase](https://supabase.com)
- Vercel CLI (`npm i -g vercel`)

### Steps

1. Push your repo to GitHub
2. Create a Neon database and copy the connection string
3. Deploy via Vercel dashboard or CLI:

```bash
vercel --prod
```

4. Add environment variables in Vercel dashboard → Project Settings → Environment Variables:

```env
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<neon-host>/<db>?sslmode=require
SECRET_KEY=<random-64-char>
JWT_SECRET=<random-64-char>
CORS_ORIGINS=https://zly-ecru.vercel.app
DEFAULT_DOMAIN=zly-ecru.vercel.app
ENVIRONMENT=production
```

5. Run migrations via Vercel CLI:

```bash
vercel env pull
alembic upgrade head
```

### Important

- The `api/index.py` file is the Vercel entrypoint (already configured)
- `vercel.json` routes all traffic to the FastAPI function
- Serverless cold starts mean the first request may take 2–3 seconds
- SQLite doesn't work on Vercel (read-only filesystem) — **must use PostgreSQL**
- No Redis available — app falls back to direct DB lookups

---

## Platform Comparison

| Feature | VPS 🥇 | Railway 🥈 | Render 🥉 | Vercel 🏅 |
|---|---|---|---|---|
| **Cost** | $5–10/mo | $5/mo+ | $7/mo+ | Free |
| **Redis** | ✅ Full | ✅ Add-on | ❌ | ❌ |
| **PostgreSQL** | ✅ Native | ✅ Add-on | ✅ Neon | ✅ Neon |
| **HTTPS** | ✅ Caddy auto | ✅ Auto | ✅ Auto | ✅ Auto |
| **Persistent storage** | ✅ Docker volume | ✅ | ✅ | ❌ ephemeral |
| **Cold starts** | ❌ None | ❌ None | ⚠️ Free tier | ⚠️ 2–3s |
| **Custom domain** | ✅ | ✅ | ✅ | ✅ |
| **Control** | Full | Medium | Medium | Low |
| **Setup time** | 15 min | 5 min | 5 min | 5 min |

---

## Reference

### All configuration variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ Yes | — | PostgreSQL connection string |
| `SECRET_KEY` | ✅ Yes | — | General purpose secret (64-char hex) |
| `JWT_SECRET` | ✅ Yes | — | JWT signing key (64-char hex) |
| `CORS_ORIGINS` | ✅ Yes | — | Allowed origins, comma-separated |
| `DEFAULT_DOMAIN` | ✅ Yes | — | Base domain for short URLs |
| `REDIS_URL` | ❌ No | `redis://localhost:6379/0` | Redis connection (graceful fallback) |
| `JWT_ALGORITHM` | ❌ No | `HS256` | Signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ No | `15` | JWT lifetime (minutes) |

### One-time setup on every platform

```bash
alembic upgrade head
```

After the first deploy, run this command to create all database tables.

### Files

| File | Purpose |
|---|---|
| `infrastructure/docker-compose.yml` | Full-stack Docker (VPS) |
| `infrastructure/Dockerfile` | Application container |
| `infrastructure/Caddyfile` | Reverse proxy + TLS |
| `infrastructure/.env.example` | Environment template |
| `api/index.py` | Vercel serverless entrypoint |
| `vercel.json` | Vercel routing config |
| `app/config.py` | All environment variables |
