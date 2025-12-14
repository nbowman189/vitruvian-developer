# Docker Implementation Guide

**Complete containerization solution for Primary Assistant**

## 📋 Overview

The Primary Assistant platform uses a production-ready Docker architecture with three containerized services:

- **PostgreSQL Database** (port 5432) - Data persistence
- **Flask Web Application** (port 8000) - Business logic
- **Nginx Reverse Proxy** (ports 80/443) - HTTP server and rate limiting

This setup provides complete isolation, scalability, and deployment consistency across environments.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              External Traffic                    │
│                (Port 80/443)                     │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │   Nginx Reverse    │  Container: primary-assistant-nginx
         │      Proxy         │  Ports: 80, 443
         │   (Alpine-based)   │  Network: frontend
         └─────────┬──────────┘
                   │ (Internal: web:8000)
         ┌─────────▼──────────┐
         │   Flask Web App    │  Container: primary-assistant-web
         │   (Gunicorn WSGI)  │  Port: 8000 (internal)
         │  (Python 3.11)     │  Networks: frontend, backend
         └─────────┬──────────┘
                   │ (Internal: db:5432)
         ┌─────────▼──────────┐
         │   PostgreSQL 15    │  Container: primary-assistant-db
         │    Database        │  Port: 5432 (internal)
         │   (Alpine-based)   │  Network: backend (internal only)
         └────────────────────┘
```

### Network Isolation

- **frontend** (bridge): Nginx accessible from host
- **backend** (bridge, internal): PostgreSQL isolated from external access

### Security Features

- Non-root user (`appuser` UID 1000) in production Flask container
- Database accessible only from backend network
- Rate limiting configured in Nginx
- Security headers enabled (XSS, clickjacking, MIME sniffing protection)
- Health checks on all services

## 🚀 Quick Start

### Development Environment

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Generate SECRET_KEY
python scripts/generate_secret_key.py

# 3. Edit .env with your configuration
nano .env

# 4. Start development environment (with hot-reload)
docker-compose -f docker-compose.dev.yml up

# 5. Access application
open http://localhost:8000
```

### Production Deployment

```bash
# 1. Configure production environment
cp .env.example .env
nano .env  # Set SECRET_KEY, POSTGRES_PASSWORD, etc.

# 2. Build and start containers
docker-compose up -d

# 3. Initialize database
docker-compose exec web flask db upgrade

# 4. Create admin user
docker-compose exec web flask create-admin

# 5. Access application
open http://localhost
```

## 📁 Docker Files Reference

### Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Production multi-container setup |
| `docker-compose.dev.yml` | Development environment with hot-reload |
| `.dockerignore` | Excludes files from Docker build context |
| `.env.example` | Environment variable template |
| `alembic.ini` | Database migration configuration |

### Dockerfiles

| File | Purpose |
|------|---------|
| `docker/Dockerfile` | Multi-stage production Flask build |
| `docker/Dockerfile.dev` | Development Flask with debugging tools |
| `docker/nginx/Dockerfile` | Nginx reverse proxy (Alpine-based) |

### Supporting Files

| File | Purpose |
|------|---------|
| `docker/nginx/nginx.conf` | Nginx configuration with rate limiting |
| `scripts/init_db.sql` | PostgreSQL initialization script |

## 🔧 Docker Compose Services

### Production (`docker-compose.yml`)

#### Database Service (`db`)
```yaml
Image: postgres:15-alpine
Container: primary-assistant-db
Port: 5432 (internal only)
Network: backend (internal)
Volumes:
  - postgres_data:/var/lib/postgresql/data
  - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
Health Check: pg_isready
```

#### Web Application Service (`web`)
```yaml
Build: docker/Dockerfile
Container: primary-assistant-web
Port: 8000 (internal)
Networks: frontend, backend
Depends On: db (healthy)
User: appuser (UID 1000)
WSGI Server: Gunicorn (4 workers)
Health Check: curl http://localhost:8000/health
```

#### Nginx Service (`nginx`)
```yaml
Build: docker/nginx/Dockerfile
Container: primary-assistant-nginx
Ports: 80:80, 443:443
Network: frontend
Depends On: web
Health Check: curl http://localhost/health
```

### Development (`docker-compose.dev.yml`)

Key differences from production:
- PostgreSQL port **5432 exposed** for DB tools access
- Flask runs with **development server** and auto-reload
- **Hot-reload** enabled through volume mounts of source code
- Relaxed security settings (debugging enabled)
- Development dependencies included (ipython, ipdb, watchdog)
- stdio/tty enabled for interactive debugging
- No non-root user restrictions

## 🐳 Dockerfile Details

### Production Flask (`docker/Dockerfile`)

**Multi-stage build** for optimized image size:

#### Builder Stage
- Base: `python:3.11-slim`
- Installs build dependencies (gcc, libpq-dev)
- Installs Python packages: Flask, SQLAlchemy, gunicorn 21.2.0, psycopg2-binary
- Creates virtual environment

#### Runtime Stage
- Base: `python:3.11-slim`
- Minimal runtime dependencies (postgresql-client, libpq5)
- **Non-root user**: `appuser` (UID 1000)
- Copies pre-built packages from builder stage
- Copies application code and documentation
- **Health check**: HTTP GET to `/health` endpoint
- **Gunicorn**: 4 workers, sync worker class

### Development Flask (`docker/Dockerfile.dev`)

- Base: `python:3.11-slim`
- Includes development tools (gcc, git, vim, curl)
- Development dependencies (flask-debugtoolbar, ipython, ipdb, watchdog)
- **Flask development server** with hot-reload and debugger
- Runs as root for convenience
- Relaxed health check settings

### Nginx (`docker/nginx/Dockerfile`)

- Base: `nginx:1.25-alpine`
- Minimal size (Alpine Linux)
- Custom nginx configuration
- SSL certificate directory prepared

## ⚙️ Nginx Configuration

### Upstream
```nginx
upstream flask_app {
    server web:8000;
}
```

### Rate Limiting

| Endpoint Pattern | Limit | Burst |
|-----------------|-------|-------|
| `/auth/*` (login) | 5 req/min | 10 |
| `/api/*` | 100 req/min | 20 |

### Security Headers

```nginx
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

### Location Blocks

- `/static/`: Direct file serving (30-day cache)
- `/uploads/`: User uploads (7-day cache)
- `/auth/`: Rate-limited authentication endpoints
- `/api/`: Rate-limited API endpoints
- `/health`: Health check (no logging)
- `/`: Proxy to Flask app with WebSocket support

### Settings
- Max upload size: **10MB**
- Logging: stdout/stderr for Docker logs
- HTTPS: Template included (commented)

## 🔐 Environment Variables

See `.env.example` for complete list. Key variables:

### Required
```bash
SECRET_KEY=generate-with-scripts/generate_secret_key.py
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=fitness_db
POSTGRES_USER=fitness_user
```

### Optional
```bash
FLASK_ENV=production
FLASK_DEBUG=False
HTTP_PORT=80
HTTPS_PORT=443
WEB_PORT=8000
LOG_LEVEL=INFO
```

## 🔨 Common Commands

### Start Services
```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up

# Rebuild after changes
docker-compose up -d --build
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx

# Last 100 lines
docker-compose logs --tail=100 web
```

### Execute Commands
```bash
# Database migrations
docker-compose exec web flask db migrate -m "Description"
docker-compose exec web flask db upgrade

# Create admin user
docker-compose exec web flask create-admin

# Python shell
docker-compose exec web python

# Database shell
docker-compose exec db psql -U fitness_user -d fitness_db

# Bash shell in container
docker-compose exec web bash
```

### Stop and Clean
```bash
# Stop services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# Remove orphaned containers
docker-compose down --remove-orphans
```

## 📊 Volume Management

### Persistent Volumes

| Volume | Purpose | Location |
|--------|---------|----------|
| `postgres_data` | Database files | `/var/lib/postgresql/data` |
| `static_files` | Static assets | `./website/static` |
| `user_uploads` | User uploads | `./website/uploads` |
| `logs` | Application logs | `./logs` |

### Backup Database
```bash
# Backup
docker-compose exec db pg_dump -U fitness_user fitness_db > backup.sql

# Restore
docker-compose exec -T db psql -U fitness_user fitness_db < backup.sql
```

## 🧪 Testing in Docker

```bash
# Run test suite
docker-compose exec web pytest

# With coverage
docker-compose exec web pytest --cov=website

# Specific test file
docker-compose exec web pytest tests/test_auth.py

# Verbose output
docker-compose exec web pytest -v
```

## 🔍 Health Checks

All services include health checks:

### Database
```bash
pg_isready -U fitness_user -d fitness_db
```

### Web Application
```bash
curl -f http://localhost:8000/health || exit 1
```

### Nginx
```bash
curl -f http://localhost/health || exit 1
```

View health status:
```bash
docker-compose ps
```

## 📈 Performance Tuning

### Gunicorn Workers

Default: 4 workers (recommended: 2-4 × CPU cores)

Adjust in `docker/Dockerfile`:
```dockerfile
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:8000", ...]
```

### PostgreSQL Connection Pooling

Configure in `.env`:
```bash
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
```

### Nginx Worker Processes

Edit `docker/nginx/nginx.conf`:
```nginx
worker_processes auto;
```

## 🐛 Troubleshooting

### Services Won't Start

1. Check logs: `docker-compose logs`
2. Verify `.env` file exists and is populated
3. Ensure ports 80, 443, 5432, 8000 are available
4. Check Docker daemon is running

### Database Connection Errors

1. Verify database is healthy: `docker-compose ps`
2. Check DATABASE_URL in `.env`
3. Wait for database initialization: `docker-compose logs db`
4. Test connection: `docker-compose exec db psql -U fitness_user -d fitness_db`

### 502 Bad Gateway

1. Check Flask app is running: `docker-compose logs web`
2. Verify health check passes: `docker-compose exec web curl http://localhost:8000/health`
3. Check Nginx upstream config: `docker-compose exec nginx cat /etc/nginx/nginx.conf`

### Hot-Reload Not Working (Dev)

1. Ensure using dev compose file: `docker-compose.dev.yml`
2. Check volume mounts in `docker-compose.dev.yml`
3. Verify Flask debug mode: `docker-compose logs web | grep DEBUG`

### Permission Denied Errors

Production uses non-root user (`appuser`). Ensure:
1. Volume mount directories are writable
2. Log directory exists: `mkdir -p logs`
3. Uploads directory exists: `mkdir -p website/uploads`

## 🚀 Production Deployment Checklist

- [ ] Set strong `SECRET_KEY` (use `scripts/generate_secret_key.py`)
- [ ] Set secure `POSTGRES_PASSWORD`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Configure SSL certificates in nginx (see `docker/nginx/nginx.conf`)
- [ ] Review rate limiting settings
- [ ] Configure backup strategy for database
- [ ] Set up log rotation
- [ ] Configure monitoring and alerts
- [ ] Review security headers
- [ ] Test database migrations
- [ ] Create admin user
- [ ] Verify health checks pass
- [ ] Load test application

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Nginx Docker Image](https://hub.docker.com/_/nginx)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

## 🆘 Support

For issues related to:
- **Database**: See `docs/database/README.md`
- **Deployment**: See `website/DEPLOYMENT_GUIDE.md`
- **Configuration**: See `website/CONFIGURATION_GUIDE.md`
- **API**: See `website/API_ENDPOINTS.md`

---

**Implementation Status**: ✅ Complete and Production-Ready

**Last Updated**: December 14, 2024
