# Remote Server Deployment Guide

## Quick Fix for "Bad Request" Error

If you're getting a **Bad Request** error when accessing the application remotely, it's because production security settings require HTTPS. Here are your options:

---

## Option 1: Development Mode (Quick Testing)

**For internal networks or testing only - NOT secure for public internet**

1. On your remote server, edit `docker-compose.yml`:
   ```yaml
   environment:
     - FLASK_ENV=development  # Change from 'production'
   ```

2. Rebuild and restart:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

3. Access via: `http://your-server-ip:8080`

⚠️ **Warning**: Development mode disables security features. Only use on trusted networks.

---

## Option 2: Production with Remote Access (Recommended)

**Keeps security features but allows HTTP access for internal deployments**

1. On your remote server, use the remote override configuration:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d
   ```

2. Access via: `http://your-server-ip:8080`

This maintains production settings but overrides:
- `SESSION_COOKIE_SECURE=false` - Allows HTTP cookies
- `SESSION_COOKIE_SAMESITE=Lax` - Allows cross-domain access

---

## Option 3: Full Production with HTTPS (Most Secure)

**For public-facing deployments**

### Prerequisites:
- Domain name pointing to your server
- SSL certificate (Let's Encrypt recommended)

### Setup:

1. Install Certbot on your server:
   ```bash
   sudo apt-get update
   sudo apt-get install certbot
   ```

2. Generate SSL certificate:
   ```bash
   sudo certbot certonly --standalone -d your-domain.com
   ```

3. Update `docker-compose.yml` to mount certificates:
   ```yaml
   services:
     nginx:
       volumes:
         - /etc/letsencrypt/live/your-domain.com:/etc/ssl/certs:ro
   ```

4. Update nginx configuration to use SSL (see `docker/nginx/nginx-ssl.conf` template)

5. Deploy:
   ```bash
   docker-compose up -d
   ```

6. Access via: `https://your-domain.com`

---

## Troubleshooting

### Still Getting Bad Request?

1. **Check environment variables:**
   ```bash
   docker-compose exec web env | grep SESSION_COOKIE
   ```

2. **View logs:**
   ```bash
   docker-compose logs web
   ```

3. **Verify config loaded:**
   ```bash
   docker-compose exec web python -c "from website import create_app; app = create_app(); print(app.config['SESSION_COOKIE_SECURE'])"
   ```

### Common Issues:

| Error | Cause | Solution |
|-------|-------|----------|
| Bad Request | HTTPS required but using HTTP | Use Option 1 or 2 above |
| Cookies not working | SameSite=Strict blocks cross-origin | Set SESSION_COOKIE_SAMESITE=Lax |
| CSRF token invalid | Different domain/IP | Ensure cookies are enabled |
| Connection refused | Port not open | Check firewall: `sudo ufw allow 8080` |

---

## Security Recommendations

### For Internal Networks (Option 2):
- ✅ Use behind VPN or firewall
- ✅ Restrict access by IP
- ✅ Use strong passwords
- ❌ Don't expose to public internet

### For Public Internet (Option 3):
- ✅ Always use HTTPS
- ✅ Enable all security headers
- ✅ Use strong SECRET_KEY
- ✅ Regular security updates
- ✅ Monitor logs for suspicious activity

---

## Environment Variables Reference

| Variable | Default (Prod) | Remote Override | Description |
|----------|---------------|-----------------|-------------|
| `FLASK_ENV` | production | development | Flask environment mode |
| `SESSION_COOKIE_SECURE` | true | false | Require HTTPS for cookies |
| `SESSION_COOKIE_SAMESITE` | Strict | Lax | Cookie cross-origin policy |
| `REMEMBER_COOKIE_SECURE` | true | false | Require HTTPS for remember-me |
| `WTF_CSRF_ENABLED` | true | true | CSRF protection (keep enabled) |

---

## Quick Commands

### Check current configuration:
```bash
docker-compose config | grep FLASK_ENV
```

### Switch to development mode:
```bash
docker-compose down
sed -i 's/FLASK_ENV=production/FLASK_ENV=development/' docker-compose.yml
docker-compose up -d
```

### Switch to remote production mode:
```bash
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d
```

### View application logs:
```bash
docker-compose logs -f web
```

### Restart after config changes:
```bash
docker-compose restart web
```
