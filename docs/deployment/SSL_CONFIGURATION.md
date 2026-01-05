# SSL/TLS Configuration

## Important: Cloudflare Handles SSL

**This project does NOT need SSL/TLS certificates on the nginx server.**

### Architecture

```
Internet → Cloudflare (SSL Termination) → nginx (HTTP only) → Flask
```

### Why No SSL on nginx?

1. **Cloudflare provides SSL termination** - All HTTPS traffic is decrypted at Cloudflare's edge
2. **Cloudflare to Origin is HTTP** - Traffic from Cloudflare to our server is plain HTTP on port 80
3. **Simpler configuration** - No need to manage Let's Encrypt certificates, renewals, or SSL configs
4. **Cloudflare advantages**:
   - Free SSL certificates (Universal SSL)
   - Automatic certificate renewal
   - Modern TLS protocols (TLS 1.3)
   - Protection against SSL vulnerabilities
   - Built-in CDN and caching

### nginx Configuration

**File:** `docker/nginx/nginx.conf`

- **Listens on:** Port 80 (HTTP only)
- **No SSL directives:** No `ssl_certificate`, `ssl_certificate_key`, or SSL listeners
- **X-Forwarded-Proto header:** Set to `https` to tell Flask the original request was HTTPS

```nginx
# HTTP server (SSL terminated by Cloudflare)
server {
    listen 80;
    server_name bowmanhomelabtech.net www.bowmanhomelabtech.net vitruvian.bowmanhomelabtech.net;

    # Tell Flask original request was HTTPS
    proxy_set_header X-Forwarded-Proto https;

    # ... rest of config
}
```

### Cloudflare SSL/TLS Settings

**Recommended Settings in Cloudflare Dashboard:**

1. **SSL/TLS Encryption Mode:** `Flexible` or `Full`
   - `Flexible`: Cloudflare → Origin is HTTP (current setup)
   - `Full`: Would require nginx to have SSL (not needed)

2. **Always Use HTTPS:** ON
   - Automatically redirects HTTP → HTTPS

3. **Minimum TLS Version:** TLS 1.2

4. **Opportunistic Encryption:** ON

5. **TLS 1.3:** ON

### Security Headers

Since Cloudflare handles SSL, nginx only needs to set application security headers:

```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Note:** HSTS (Strict-Transport-Security) is handled by Cloudflare, not nginx.

### Flask Configuration

Flask must trust the `X-Forwarded-Proto` header from nginx:

```python
# config.py
PREFERRED_URL_SCHEME = 'https'  # For URL generation
SESSION_COOKIE_SECURE = True    # Requires HTTPS for session cookies
```

### Docker Compose

**Production compose file:** `docker-compose.remote.yml`

- nginx exposes port 80 (no 443)
- No volume mounts for SSL certificates
- No Let's Encrypt container

### Common Mistakes to Avoid

❌ **Don't add SSL certificates to nginx** - Unnecessary and adds complexity
❌ **Don't use `listen 443 ssl`** - Cloudflare terminates SSL
❌ **Don't set up Let's Encrypt** - Cloudflare provides certificates
❌ **Don't set Cloudflare SSL mode to `Full (strict)`** - nginx doesn't have a valid certificate

### Troubleshooting

**Problem:** Mixed content warnings (HTTP resources on HTTPS page)

**Solution:** Ensure all asset URLs use relative paths or HTTPS

---

**Problem:** Infinite redirect loops

**Solution:** Check that nginx sets `X-Forwarded-Proto: https` header

---

**Problem:** Session cookies not working

**Solution:** Verify `SESSION_COOKIE_SECURE = True` and Flask sees HTTPS via X-Forwarded-Proto

### References

- [Cloudflare SSL/TLS Overview](https://developers.cloudflare.com/ssl/)
- [Cloudflare SSL Modes](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/)
- [nginx as a reverse proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)

## Last Updated

January 2, 2026 - Documented during dashboard deployment troubleshooting
