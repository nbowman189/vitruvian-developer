# Nginx Container Unhealthy - Troubleshooting

**Error**: `ERROR: for nginx Container "3bc24a844d90" is unhealthy.`

## 🔍 Diagnosis Steps

Run these commands on your server to diagnose the issue:

### Step 1: Check Container Status
```bash
docker-compose ps
```

**Expected**:
- `db` should be "Up (healthy)"
- `web` should be "Up (healthy)"
- `nginx` is showing unhealthy

### Step 2: Check Nginx Logs
```bash
docker-compose logs nginx | tail -50
```

**Look for**:
- Connection errors to web container
- Proxy errors
- Timeout errors

### Step 3: Check Web Container Logs
```bash
docker-compose logs web | tail -50
```

**Look for**:
- Flask application startup errors
- Health check endpoint errors
- Any Python exceptions

### Step 4: Test Web Container Directly
```bash
# Test if web container responds on its internal port
docker-compose exec web curl -v http://localhost:8000/api/health
```

**Expected**: Should return JSON with `{"status": "healthy", ...}`

### Step 5: Test Nginx → Web Connection
```bash
# Test if nginx can reach web container
docker-compose exec nginx curl -v http://web:8000/api/health
```

**Expected**: Should return same JSON response

### Step 6: Test Full Chain
```bash
# Test nginx from outside (this is what the health check does)
curl -v http://localhost/api/health
```

**Expected**: Should return health status through nginx proxy

---

## 🔧 Common Issues & Fixes

### Issue 1: Web Container Not Healthy Yet
**Symptom**: Nginx starts before web is fully healthy

**Fix**: Wait for web container to be healthy first
```bash
# Check if web is healthy
docker-compose ps web

# If not healthy, check web logs
docker-compose logs web

# Common cause: Missing environment variables or database connection issues
```

### Issue 2: Network Connectivity
**Symptom**: Nginx can't reach web container on `web:8000`

**Fix**: Verify networks are properly configured
```bash
# Check networks
docker network ls

# Inspect frontend network
docker network inspect vitruvian-developer_frontend

# Both nginx and web should be in this network
```

### Issue 3: Health Check Timeout
**Symptom**: Health check takes too long, times out before responding

**Current config**: 30s interval, 10s timeout, 3 retries

**Fix**: Temporarily increase timeout in docker-compose.yml
```yaml
nginx:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost/api/health"]
    interval: 30s
    timeout: 30s  # Increase from 10s
    retries: 5    # Increase from 3
```

### Issue 4: Web Container Health Check Failing
**Symptom**: Web container itself isn't healthy, so nginx dependency fails

**Check**:
```bash
docker-compose ps web
# If not healthy, web container is the root problem
```

**Fix**: Debug web container first (see Issue 5)

### Issue 5: Flask App Not Starting
**Symptom**: Web container runs but Flask doesn't start or crashes

**Check logs**:
```bash
docker-compose logs web | grep -i error
```

**Common causes**:
- Missing `.env` file or environment variables
- `SECRET_KEY` not set
- `POSTGRES_PASSWORD` not set
- Database connection failure
- Python import errors (missing dependencies)

**Fix**:
```bash
# Verify .env exists
ls -la .env

# Check required variables are set
grep SECRET_KEY .env
grep POSTGRES_PASSWORD .env

# Ensure they're not the placeholder values
```

---

## 🚨 Most Likely Issue

Based on the error, the **most likely cause** is:

**The web container health check is failing**, which means nginx's dependency (`depends_on: web: condition: service_healthy`) is never satisfied.

### Quick Fix Steps:

1. **Check web container status**:
   ```bash
   docker-compose ps web
   ```

2. **If web is unhealthy, check its logs**:
   ```bash
   docker-compose logs web
   ```

3. **Look for these specific errors**:
   - `SECRET_KEY must be set` - Fix: Set SECRET_KEY in .env
   - `POSTGRES_PASSWORD must be set` - Fix: Set POSTGRES_PASSWORD in .env
   - `ModuleNotFoundError` - Fix: Dependencies not installed (rebuild)
   - Database connection errors - Fix: Check db container is healthy

4. **Fix the error and restart**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## 📋 Full Diagnostic Script

Run this complete diagnostic:

```bash
#!/bin/bash
echo "=== DOCKER HEALTH DIAGNOSTICS ==="
echo ""

echo "1. Container Status:"
docker-compose ps
echo ""

echo "2. Environment File:"
if [ -f .env ]; then
    echo "✅ .env exists"
    echo "SECRET_KEY set: $(grep -q 'SECRET_KEY=your-secret' .env && echo '❌ Using placeholder!' || echo '✅')"
    echo "POSTGRES_PASSWORD set: $(grep -q 'POSTGRES_PASSWORD=your-secure' .env && echo '❌ Using placeholder!' || echo '✅')"
else
    echo "❌ .env file missing!"
fi
echo ""

echo "3. Database Container:"
docker-compose exec db pg_isready -U postgres -d primary_assistant
echo ""

echo "4. Web Container Health:"
docker-compose exec web curl -f http://localhost:8000/api/health 2>/dev/null && echo "✅ Web healthy" || echo "❌ Web unhealthy"
echo ""

echo "5. Nginx → Web Connection:"
docker-compose exec nginx curl -f http://web:8000/api/health 2>/dev/null && echo "✅ Nginx can reach web" || echo "❌ Cannot reach web"
echo ""

echo "6. Recent Errors (Web):"
docker-compose logs web | grep -i error | tail -10
echo ""

echo "7. Recent Errors (Nginx):"
docker-compose logs nginx | grep -i error | tail -10
```

---

## 🎯 Action Plan

1. **Run diagnostic script above**
2. **Share the output** so we can identify the exact issue
3. **Most likely fix**: Set proper values in `.env` file
4. **Rebuild and restart**: `docker-compose down && docker-compose up -d`

---

**Need the output from the diagnostic commands to proceed with the fix!**
