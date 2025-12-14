# Deployment and Launch Guide - Phase 8

**Version**: 1.0
**Status**: Production Ready
**Last Updated**: November 17, 2025

---

## Overview

This guide covers deploying "The Vitruvian Developer" Flask application to production. The application has been hardened with security fixes, error handling improvements, and performance optimizations.

---

## Pre-Deployment Checklist

### 1. Environment Configuration

Create or update `.env` file in the project root:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security
SECRET_KEY=your-secure-random-key-here

# Contact Information (optional)
CONTACT_EMAIL=nbowman189@gmail.com
CONTACT_LINKEDIN=https://www.linkedin.com/in/nathan-bowman-b27484103/
CONTACT_GITHUB=https://github.com/nbowman189
```

**Generate SECRET_KEY**:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Dependencies Installation

```bash
# Install all required packages
pip install -r requirements.txt

# Core dependencies:
# - Flask
# - markdown2
# - psutil (for performance monitoring)
# - python-dotenv (optional, for .env support)
```

### 3. Project Structure Verification

```
website/
├── app.py                          # Main application
├── app_refactored.py              # Modular architecture (alternative)
├── config.py                      # Configuration management
├── requirements.txt               # Dependencies
├── static/                        # Static files (CSS, JS, images)
│   ├── css/style.css
│   ├── js/script.js
│   └── ...
├── templates/                     # HTML templates
│   ├── base.html
│   ├── index.html
│   └── ...
├── routes/                        # API routes (modular)
│   ├── __init__.py
│   ├── main.py
│   ├── blog.py
│   ├── api_blog.py
│   ├── api_projects.py
│   ├── api_misc.py
│   └── api_monitoring.py
├── utils/                         # Utility modules
│   ├── __init__.py
│   ├── file_utils.py
│   ├── cache.py
│   ├── pagination.py
│   ├── performance.py
│   └── error_handler.py
├── blog/                          # Blog markdown files
│   └── *.md
└── PERFORMANCE.md                 # Performance documentation
```

---

## Deployment Options

### Option 1: Traditional Server (Recommended for Getting Started)

#### Using Gunicorn (Production WSGI Server)

**Installation**:
```bash
pip install gunicorn
```

**Start Server**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Parameters**:
- `-w 4`: Number of worker processes (adjust based on CPU cores)
- `-b 0.0.0.0:5000`: Bind to all interfaces on port 5000
- `app:app`: Application module and object

**Recommended for Production**:
```bash
gunicorn \
  --workers 4 \
  --worker-class sync \
  --timeout 30 \
  --bind 0.0.0.0:5000 \
  --access-logfile - \
  --error-logfile - \
  app:app
```

#### Using Systemd (For Auto-start and Management)

Create `/etc/systemd/system/vitruvian.service`:

```ini
[Unit]
Description=The Vitruvian Developer - Portfolio Website
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/vitruvian
Environment="FLASK_ENV=production"
Environment="FLASK_DEBUG=false"
ExecStart=/usr/local/bin/gunicorn \
    --workers 4 \
    --timeout 30 \
    --bind 127.0.0.1:5000 \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vitruvian
sudo systemctl start vitruvian
sudo systemctl status vitruvian
```

### Option 2: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Set environment
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')"

# Start application
CMD ["gunicorn", "--workers", "4", "--timeout", "30", "--bind", "0.0.0.0:5000", "app:app"]
```

**Build and Run**:
```bash
# Build image
docker build -t vitruvian:latest .

# Run container
docker run -d \
  --name vitruvian \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e FLASK_DEBUG=false \
  vitruvian:latest

# View logs
docker logs -f vitruvian

# Stop container
docker stop vitruvian
```

### Option 3: Nginx Reverse Proxy (Recommended for Production)

**Install Nginx**:
```bash
sudo apt-get install nginx
```

**Configure `/etc/nginx/sites-available/vitruvian`**:

```nginx
upstream vitruvian_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Certificate Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers (Nginx level)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy Configuration
    location / {
        proxy_pass http://vitruvian_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (optimize)
    location /static/ {
        alias /var/www/vitruvian/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Disable access to sensitive files
    location ~ /\. {
        deny all;
    }

    location ~ \.py$ {
        deny all;
    }
}
```

**Enable Site**:
```bash
sudo ln -s /etc/nginx/sites-available/vitruvian /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Install SSL Certificate (Let's Encrypt)**:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com
```

---

## Security Hardening for Production

### 1. Environment Variables

```bash
# Set secure defaults
export FLASK_ENV=production
export FLASK_DEBUG=false
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

### 2. Verify Security Headers

```bash
# Check all security headers are present
curl -i https://your-domain.com/ | grep -E "X-Frame|X-Content|X-XSS|HSTS"

# Expected output:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 3. Path Traversal Prevention Verification

```bash
# This should return 403 Forbidden
curl https://your-domain.com/api/project/Health_and_Fitness/file/../../etc/passwd.md

# Expected response:
# {"error": "Access denied"}
```

### 4. Debug Mode Verification

```bash
# Verify debug mode is disabled
curl -s https://your-domain.com/invalid-route | grep -i "debugger\|traceback"

# Should return clean JSON error, not HTML traceback
```

### 5. File Permissions

```bash
# Set correct permissions
sudo chown -R www-data:www-data /var/www/vitruvian
sudo chmod -R 755 /var/www/vitruvian
sudo chmod -R 755 /var/www/vitruvian/static
```

---

## Performance Monitoring

### Health Check Endpoint

```bash
# Monitor application health
curl https://your-domain.com/api/health

# Response:
# {
#   "status": "healthy",
#   "memory_mb": 45.2,
#   "cpu_percent": 2.3
# }
```

### Performance Metrics

```bash
# Get full metrics
curl https://your-domain.com/api/metrics/full

# Get endpoint performance
curl https://your-domain.com/api/metrics/endpoints

# Get cache performance
curl https://your-domain.com/api/metrics/cache
```

### Monitoring Setup (Optional)

**Using Prometheus**:
```bash
pip install prometheus-client
```

Add to `app.py`:
```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('http_requests_total', 'Total HTTP Requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP Request Duration')

@app.before_request
def before_request():
    request.start_time = time.time()
    request_count.inc()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        request_duration.observe(duration)
    return response

@app.route('/metrics')
def metrics():
    return generate_latest()
```

---

## Logging Configuration

### Log Rotation

Create `/etc/logrotate.d/vitruvian`:

```
/var/www/vitruvian/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload vitruvian > /dev/null 2>&1 || true
    endscript
}
```

### Log Monitoring

```bash
# Real-time application logs
tail -f /var/www/vitruvian/logs/app.log

# Error logs
tail -f /var/www/vitruvian/logs/error.log

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log
```

---

## Backup and Recovery

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups/vitruvian"
SOURCE_DIR="/var/www/vitruvian"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup application
tar -czf $BACKUP_DIR/vitruvian_$DATE.tar.gz $SOURCE_DIR

# Keep last 7 backups
find $BACKUP_DIR -name "vitruvian_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/vitruvian_$DATE.tar.gz"
```

**Schedule with Cron**:
```bash
0 2 * * * /var/www/vitruvian/backup.sh
```

### Recovery Procedure

```bash
# List available backups
ls -la /backups/vitruvian/

# Restore from backup
tar -xzf /backups/vitruvian/vitruvian_20251117_020000.tar.gz -C /

# Restart application
sudo systemctl restart vitruvian
```

---

## Troubleshooting

### Common Issues

#### 1. 403 Forbidden on Static Files

**Problem**: Static files return 403
```bash
sudo chmod -R 755 /var/www/vitruvian/static
sudo chown -R www-data:www-data /var/www/vitruvian/static
```

#### 2. 502 Bad Gateway

**Problem**: Nginx can't connect to Flask app
```bash
# Check if Flask is running
ps aux | grep gunicorn

# Restart Flask
sudo systemctl restart vitruvian

# Check Nginx error logs
tail -f /var/log/nginx/error.log
```

#### 3. High Memory Usage

**Problem**: Application using excessive memory
```bash
# Check memory metrics
curl https://your-domain.com/api/metrics/full

# Restart application
sudo systemctl restart vitruvian

# Check cache stats
curl https://your-domain.com/api/metrics/cache
```

#### 4. Slow Response Times

**Problem**: API endpoints responding slowly
```bash
# Check endpoint performance
curl https://your-domain.com/api/metrics/endpoints

# Check if slowest endpoints are cached
# Results should show sub-100ms response times for cached endpoints
```

### Debug Mode (Development Only)

**Never enable in production**, but if needed for troubleshooting:

```bash
# Temporarily enable debug
FLASK_DEBUG=true FLASK_ENV=development python app.py

# Check application logs
tail -f app.log
```

---

## Post-Deployment Verification

### Run Complete Verification

```bash
#!/bin/bash

echo "Running post-deployment verification..."

# 1. Health check
echo "1. Checking health endpoint..."
curl -s https://your-domain.com/api/health | jq .

# 2. Security headers
echo "2. Verifying security headers..."
curl -I https://your-domain.com/ | grep -E "X-Frame|X-Content|X-XSS|HSTS"

# 3. Path traversal blocking
echo "3. Testing path traversal protection..."
response=$(curl -s -o /dev/null -w "%{http_code}" https://your-domain.com/api/project/test/file/../../etc/passwd.md)
if [ "$response" = "403" ]; then
  echo "✓ Path traversal blocked (403)"
else
  echo "✗ Path traversal not blocked (got $response)"
fi

# 4. API endpoints
echo "4. Testing API endpoints..."
curl -s https://your-domain.com/api/blog/posts | jq .page

# 5. Static files
echo "5. Checking static files..."
curl -I https://your-domain.com/static/css/style.css | head -1

echo "Verification complete!"
```

---

## Rollback Procedure

If issues occur after deployment:

```bash
# 1. Check backup exists
ls -la /backups/vitruvian/

# 2. Stop application
sudo systemctl stop vitruvian

# 3. Restore backup
sudo tar -xzf /backups/vitruvian/vitruvian_YYYYMMDD_HHMMSS.tar.gz -C /

# 4. Start application
sudo systemctl start vitruvian

# 5. Verify
curl https://your-domain.com/api/health
```

---

## Performance Tuning

### Gunicorn Worker Configuration

**4-core server**:
```bash
gunicorn -w 9 -k sync app:app  # (2 * CPU cores) + 1
```

**High-traffic server**:
```bash
gunicorn -w 4 -k gevent -w 1000 app:app  # Use gevent workers
```

### Cache Configuration

Adjust cache timeouts in `routes/api_blog.py`:

```python
# Current defaults:
- Latest posts: 300s (5 minutes)
- Blog post content: 3600s (1 hour)
- Related projects: 3600s (1 hour)

# For high-traffic: increase to 3600s (1 hour) for latest posts
cache.set(cache_key, posts, timeout=3600)
```

### Database Connection Pooling

If using database backend instead of files:
```python
from sqlalchemy.pool import QueuePool

db = SQLAlchemy(
    engine_options={
        "poolclass": QueuePool,
        "pool_size": 10,
        "max_overflow": 20,
    }
)
```

---

## Summary

**Phase 8 Deployment Complete** ✅

Your application is now:
- ✅ Security hardened against common vulnerabilities
- ✅ Error handling standardized and production-ready
- ✅ Performance optimized with caching and efficient algorithms
- ✅ Thread-safe and scalable for concurrent users
- ✅ Monitored with health checks and metrics endpoints
- ✅ Ready for production deployment

**Recommended Next Steps**:
1. Deploy to staging environment first
2. Run security audit (penetration testing)
3. Load test with expected traffic
4. Monitor error logs for first 24 hours
5. Fine-tune performance parameters based on metrics

---

**Deployment Guide Version**: 1.0
**Last Updated**: November 17, 2025
**Maintained by**: Development Team
