# Deployment Guide — Zly

This guide covers production deployment of Zly with Docker Compose, Caddy reverse proxy, PostgreSQL, and Redis.

## Prerequisites

- Linux VPS (Ubuntu 22.04+ or Debian 12+ recommended)
- Docker Engine 24+ and Docker Compose v2
- A domain name pointing to your server (e.g., `zly.example.com`)
- For custom domains: ability to add DNS records (CNAME + TXT)

## Quick Deploy

```bash
# Clone the repository
git clone https://github.com/your-org/zly.git
cd zly

# Create production environment file
cp infrastructure/.env.example .env
# Edit .env with secure secrets

# Start all services
docker compose -f infrastructure/docker-compose.yml up -d

# Run database migrations
docker compose -f infrastructure/docker-compose.yml exec fastapi alembic upgrade head

# Check logs
docker compose -f infrastructure/docker-compose.yml logs -f
```

## Environment Configuration

Create `.env` in the project root:

```env
# Database
DATABASE_URL=postgresql+asyncpg://zly:your-db-password@postgres:5432/zly

# Redis (optional, app degrades gracefully)
REDIS_URL=redis://redis:6379/0

# Secrets — generate with: openssl rand -hex 64
SECRET_KEY=<64-char-hex>
JWT_SECRET=<64-char-hex>

# Security
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Networking
CORS_ORIGINS=https://zly.example.com
DEFAULT_DOMAIN=zly.example.com

# Production flag
ENVIRONMENT=production
```

## Docker Compose (Production)

The `infrastructure/docker-compose.yml` includes:

- **postgres** — PostgreSQL 16 Alpine with persistent volume
- **redis** — Redis 7 Alpine with persistent volume
- **caddy** — Caddy v2 reverse proxy with auto-Let's Encrypt TLS
- **fastapi** — Zly application server with health checks

All services share an internal Docker network. Caddy exposes ports 80 and 443.

## Caddy Configuration

The `infrastructure/Caddyfile` handles:

- Automatic TLS via Let's Encrypt
- Reverse proxy to the FastAPI container
- Static file serving for QR codes and assets
- Security headers

For production, update the domain:

```
zly.example.com {
    reverse_proxy fastapi:8000
}
```

## Security Hardening

### Required

- Generate secure random secrets: `openssl rand -hex 64`
- Set `JWT_SECRET` to at least 32 bytes of random data
- Change `POSTGRES_PASSWORD` in docker-compose.yml
- Set `CORS_ORIGINS` to your exact domain (not `*`)
- Use `ENVIRONMENT=production` in .env
- Never commit `.env` to version control

### Recommended

- Add rate limiting middleware (see below)
- Set up fail2ban for SSH
- Use Docker's built-in health checks
- Enable Docker content trust
- Regular security updates via unattended-upgrades

### Rate Limiting (via Caddy)

Add to your Caddyfile:

```caddy
zly.example.com {
    rate_limit {
        zone api {
            key {remote_host}
            events 100
            window 1m
        }
        zone redirect {
            key {remote_host}
            events 500
            window 1m
        }
    }
    reverse_proxy fastapi:8000
}
```

## Database

### Migrations

```bash
# Run migrations
docker compose exec fastapi alembic upgrade head

# View migration history
docker compose exec fastapi alembic history

# Create a new migration (after model changes)
docker compose exec fastapi alembic revision --autogenerate -m "description"
```

### Backup

```bash
# Automated backup script (add to cron)
docker compose exec postgres pg_dump -U zly zly > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
cat backup.sql | docker compose exec -T postgres psql -U zly zly
```

## Monitoring

### Health Check

```
GET /health
```

Returns `{"status": "ok"}` when the application is running.

### Logs

```bash
# All services
docker compose logs -f

# Single service
docker compose logs -f fastapi

# Last 100 lines
docker compose logs --tail=100 fastapi
```

### Resource Monitoring

```bash
docker stats
```

### Application Metrics

- Uptime via `/health` endpoint
- Database connection pool size in logs
- Redis cache hit rate (via Redis CLI: `docker compose exec redis redis-cli info stats`)

## Upgrades

```bash
# Pull latest image
docker compose pull

# Recreate containers
docker compose up -d --force-recreate

# Run any new migrations
docker compose exec fastapi alembic upgrade head
```

## Troubleshooting

### Database connection fails

```bash
# Verify PostgreSQL is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres
```

### 502 Bad Gateway from Caddy

```bash
# Verify FastAPI is running
docker compose ps fastapi

# Check FastAPI logs
docker compose logs fastapi

# Test FastAPI directly (internal port)
curl http://localhost:8000/health
```

### Migrations fail

```bash
# Check current migration state
docker compose exec fastapi alembic current

# View migration history
docker compose exec fastapi alembic history

# Manually stamp a revision
docker compose exec fastapi alembic stamp head
```

### SSL certificate issues

Caddy auto-provisions certificates. If issues arise:

```bash
# Check Caddy logs
docker compose logs caddy

# Manually request certificate
docker compose exec caddy caddy renew

# Test certificate renewal
docker compose exec caddy caddy renew --force
```

## Scaling

For high-traffic deployments:

- Increase FastAPI workers: `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]`
- Add a dedicated Redis cluster for caching
- Use a managed PostgreSQL service (RDS, Cloud SQL)
- Add a CDN for static assets and QR codes
- Load balance across multiple FastAPI instances with Caddy

## Reference

| File | Purpose |
|---|---|
| `infrastructure/docker-compose.yml` | Service orchestration |
| `infrastructure/Dockerfile` | Application container |
| `infrastructure/Caddyfile` | Reverse proxy + TLS |
| `infrastructure/.env.example` | Environment template |
| `app/config.py` | Runtime configuration |
