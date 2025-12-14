# Docker Configuration Issues - Critical Fixes Required

**Date**: December 14, 2024
**Status**: ❌ DEPLOYMENT FAILS - Multiple Critical Issues Found
**Priority**: HIGH - Blocks all deployments

---

## 🔴 Critical Issues Found

### Issue 1: Incorrect Health Check Endpoints
**Severity**: CRITICAL - Prevents containers from starting

**Problem**:
- Docker health checks try to access `/health`
- Actual endpoint is `/api/health` (registered under API blueprint)

**Location**:
- `docker-compose.yml` line 60: `http://localhost:8000/health`
- `docker-compose.yml` line 87: `http://localhost/health`
- `docker/Dockerfile` line 63: `http://localhost:8000/health`

**Fix**:
Change all health check URLs from `/health` to `/api/health`

---

### Issue 2: Missing Dependencies
**Severity**: CRITICAL - Health checks will fail even with correct endpoint

**Problem**:
- Health check endpoint requires `psutil` package
- `psutil` is NOT in `website/requirements.txt`
- Health check will crash with ImportError

**Location**:
- `website/routes/api_monitoring.py` lines 10-11, 21, 25, 52-53
- `website/requirements.txt` - missing `psutil`

**Fix**:
Add to `website/requirements.txt`:
```
# System Monitoring (for health checks)
psutil>=5.9.0,<6.0.0
```

---

### Issue 3: Missing curl in Docker Image
**Severity**: CRITICAL - Health checks cannot execute

**Problem**:
- Dockerfile health check uses `curl` command
- `python:3.11-slim` base image does NOT include curl
- Health checks will fail with "curl: command not found"

**Location**:
- `docker/Dockerfile` line 63
- `docker-compose.yml` lines 60, 87

**Fix Option 1** (Recommended - use Python):
Replace curl with Python in Dockerfile line 63:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()" || exit 1
```

**Fix Option 2** (Install curl):
Add curl installation in Dockerfile line 33-36:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

---

### Issue 4: Missing SSL Directory
**Severity**: MEDIUM - Nginx container won't start

**Problem**:
- `docker-compose.yml` line 79 mounts `./docker/nginx/ssl:/etc/nginx/ssl:ro`
- Directory `/docker/nginx/ssl` does NOT exist
- Volume mount will fail if directory doesn't exist

**Location**:
- `docker-compose.yml` line 79

**Fix**:
Create the directory or make mount optional:
```bash
mkdir -p docker/nginx/ssl
```

OR remove/comment the line until SSL is configured

---

### Issue 5: Project Documentation Path Issues
**Severity**: MEDIUM - Application may not find project files

**Problem**:
- Dockerfile copies: `COPY AI_Development/docs/ ../AI_Development/docs/`
- This copies to `/AI_Development/docs/` (outside /app directory)
- App.py expects projects at `../AI_Development/` relative to /app/website
- Path structure is inconsistent

**Location**:
- `docker/Dockerfile` lines 51-52
- `website/app.py` line 11: `PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`

**Fix**:
The Dockerfile should copy to correct location:
```dockerfile
# Copy project documentation to parent directory structure
COPY --chown=appuser:appuser AI_Development/ /AI_Development/
COPY --chown=appuser:appuser Health_and_Fitness/ /Health_and_Fitness/
```

---

### Issue 6: Database Variable Naming Inconsistency
**Severity**: LOW - Causes confusion

**Problem**:
- `.env.example` uses: `portfolio_user`, `portfolio_db`
- `docker-compose.yml` defaults: `primary_assistant`
- Inconsistent naming causes confusion

**Location**:
- `.env.example` lines 25-27
- `docker-compose.yml` lines 10, 12, 20, 40

**Fix**:
Update `.env.example` to match docker-compose defaults:
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-database-password-here
POSTGRES_DB=primary_assistant
```

---

### Issue 7: Web Service FLASK_APP Path
**Severity**: LOW - May cause startup issues

**Problem**:
- `docker-compose.yml` line 35: `FLASK_APP=app.py`
- Working directory is `/app` which contains website code
- This should work, but could be more explicit

**Location**:
- `docker-compose.yml` line 35

**Fix** (Optional - for clarity):
```yaml
- FLASK_APP=website.app:app
```

---

## 📋 Summary of Required Fixes

### Immediate Actions (CRITICAL):

1. ✅ **Fix health check endpoints** - Change `/health` to `/api/health` everywhere
2. ✅ **Add psutil dependency** - Add to requirements.txt
3. ✅ **Fix curl in health checks** - Use Python instead of curl OR install curl
4. ✅ **Create SSL directory** - `mkdir -p docker/nginx/ssl`

### Recommended Actions (MEDIUM):

5. ✅ **Fix project paths** - Copy full project directories to root
6. ✅ **Update .env.example** - Match docker-compose defaults

---

## 🔧 Files That Need Changes

### File 1: `docker-compose.yml`
**Lines to change**:
- Line 60: `http://localhost:8000/health` → `http://localhost:8000/api/health`
- Line 79: Comment out or create `docker/nginx/ssl` directory
- Line 87: `http://localhost/health` → `http://localhost/api/health`

### File 2: `docker/Dockerfile`
**Lines to change**:
- Line 33-36: Add curl OR keep Python health check but fix URL
- Line 51-52: Fix project documentation copy paths
- Line 63: `http://localhost:8000/health` → `http://localhost:8000/api/health`

### File 3: `website/requirements.txt`
**Add**:
```
# System Monitoring (for health checks)
psutil>=5.9.0,<6.0.0
```

### File 4: `.env.example`
**Lines to change**:
- Line 25: `POSTGRES_USER=postgres`
- Line 27: `POSTGRES_DB=primary_assistant`

### File 5: Create directory
```bash
mkdir -p docker/nginx/ssl
touch docker/nginx/ssl/.gitkeep
```

---

## ✅ Testing Checklist (After Fixes)

Before deployment:

```bash
# 1. Apply all fixes above

# 2. Build images
docker-compose build

# 3. Start services
docker-compose up -d

# 4. Check all containers are healthy
docker-compose ps
# All should show "Up (healthy)"

# 5. Test health endpoint directly
curl http://localhost/api/health
# Should return: {"status": "healthy", ...}

# 6. Check logs for errors
docker-compose logs web
docker-compose logs db
docker-compose logs nginx

# 7. Verify application loads
curl http://localhost/
```

---

## 🚀 Quick Fix Script

Save this as `fix-docker.sh` and run it:

```bash
#!/bin/bash
echo "Fixing Docker configuration..."

# Create SSL directory
mkdir -p docker/nginx/ssl
touch docker/nginx/ssl/.gitkeep

# Add psutil to requirements.txt (if not already there)
if ! grep -q "psutil" website/requirements.txt; then
    echo "" >> website/requirements.txt
    echo "# System Monitoring (for health checks)" >> website/requirements.txt
    echo "psutil>=5.9.0,<6.0.0" >> website/requirements.txt
    echo "✅ Added psutil to requirements.txt"
fi

echo "✅ SSL directory created"
echo ""
echo "⚠️  MANUAL FIXES STILL REQUIRED:"
echo "1. Edit docker-compose.yml - change /health to /api/health (3 places)"
echo "2. Edit docker/Dockerfile - change /health to /api/health (1 place)"
echo "3. Edit .env.example - update database names"
echo ""
echo "See DOCKER_ISSUES_REPORT.md for complete details"
```

---

## 📞 Root Cause

The Docker configuration was created but never tested on a fresh system. These issues would all appear immediately on first deployment:

1. Services fail health checks → never become "healthy"
2. Dependent services wait forever for upstream to be healthy
3. Entire stack fails to start

**Recommended**: Always test Docker configs locally before pushing to production.

---

**Status**: Awaiting fixes to proceed with deployment
**Next Steps**: Apply fixes above, then retry deployment
