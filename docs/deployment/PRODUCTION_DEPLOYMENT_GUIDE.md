# Production Deployment Guide
**Domain:** bowmanhomelabtech.net
**Server:** Ubuntu 24.04 LTS
**Date:** December 16, 2024

---

## 🎯 Overview

This guide will help you complete the production deployment of your Primary Assistant application with:
- ✅ HTTPS with Let's Encrypt SSL certificates
- ✅ Domain configuration (bowmanhomelabtech.net)
- ✅ Automated database backups
- ✅ Health data import from local to remote

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:
- [x] DNS A record pointing bowmanhomelabtech.net to your server IP
- [x] DNS propagation complete (test with: `dig bowmanhomelabtech.net`)
- [x] SSH access to your remote server
- [x] Docker containers currently running (HTTP on port 8080)
- [x] Admin user created and tested

---

## 🚀 Deployment Steps

### Step 1: Configure DNS (If Not Done Already)

**Log into your domain registrar** and add these DNS records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 3600 |
| A | www | YOUR_SERVER_IP | 3600 |

**Verify DNS propagation:**
```bash
# From your local machine or remote server
dig bowmanhomelabtech.net +short
# Should return your server IP

dig www.bowmanhomelabtech.net +short
# Should return your server IP
```

DNS propagation typically takes 5-60 minutes.

---

### Step 2: Deploy Updated Code to Remote Server

SSH into your remote server and pull the latest changes:

```bash
# SSH into your server
ssh nathan@your-server-ip

# Navigate to project directory
cd /home/nathan/vitruvian-developer

# Pull latest code
git pull origin main

# Verify the new files exist
ls -la scripts/setup-ssl.sh
ls -la scripts/import-health-data.py
ls -la scripts/backup-database.sh
```

---

### Step 3: Set Up HTTPS with Let's Encrypt

Run the automated SSL setup script:

```bash
# Make sure you're in the project directory
cd /home/nathan/vitruvian-developer

# Run the SSL setup script as root
sudo ./scripts/setup-ssl.sh
```

**What this script does:**
1. Installs Certbot (if not already installed)
2. Creates required directories for SSL certificates
3. Checks DNS configuration
4. Temporarily modifies nginx for HTTP verification
5. Obtains SSL certificates from Let's Encrypt
6. Restores production HTTPS nginx config
7. Restarts containers with HTTPS enabled
8. Sets up automatic certificate renewal (cron job)

**Expected output:**
```
✅ SSL Setup Complete!

Your site is now accessible at:
  🌐 https://bowmanhomelabtech.net
  🌐 https://www.bowmanhomelabtech.net

Certificate details:
  📁 Location: /etc/letsencrypt/live/bowmanhomelabtech.net/
  📅 Expires: 2025-03-16 (auto-renews)
```

**If the script fails**, you can manually obtain certificates:

```bash
# Stop containers
docker-compose down

# Obtain certificate manually
sudo certbot certonly --standalone \
  --preferred-challenges http \
  -d bowmanhomelabtech.net \
  -d www.bowmanhomelabtech.net

# Start containers with HTTPS
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d
```

---

### Step 4: Verify HTTPS is Working

Test your HTTPS deployment:

```bash
# Test HTTPS endpoint
curl -I https://bowmanhomelabtech.net

# Should return: HTTP/2 200

# Test HTTP redirect
curl -I http://bowmanhomelabtech.net

# Should return: HTTP/1.1 301 Moved Permanently
# Location: https://bowmanhomelabtech.net/
```

**Open in browser:**
1. Go to `https://bowmanhomelabtech.net`
2. Check for the lock icon in the address bar
3. Click the lock to verify certificate details
4. Test login functionality

**Check SSL rating:**
- Visit: https://www.ssllabs.com/ssltest/
- Enter: `bowmanhomelabtech.net`
- Wait for scan to complete
- You should get an **A or A+** rating

---

### Step 5: Import Health Data

Now that HTTPS is working, import your health data from local to remote.

**Option A: Import from Remote Server (Recommended)**

First, copy your check-in-log.md to the server:

```bash
# From your LOCAL machine
scp ~/primary-assistant/Health_and_Fitness/data/check-in-log.md \
  nathan@your-server-ip:/home/nathan/check-in-log.md
```

Then on the remote server:

```bash
# SSH into server
ssh nathan@your-server-ip

cd /home/nathan/vitruvian-developer

# Run import script
docker-compose exec web python scripts/import-health-data.py /home/nathan/check-in-log.md
```

**Option B: Import via SSH Tunnel (Alternative)**

Set up an SSH tunnel to access the remote database from your local machine:

```bash
# From your LOCAL machine
ssh -L 5433:localhost:5432 nathan@your-server-ip

# In another terminal
cd ~/primary-assistant
python3 scripts/import-health-data.py
```

**Verify import:**

```bash
# Check how many health metrics were imported
docker-compose exec web python -c "
from website import create_app, db
from website.models.health import HealthMetric
app = create_app()
with app.app_context():
    count = HealthMetric.query.count()
    print(f'Total health metrics: {count}')
    latest = HealthMetric.query.order_by(HealthMetric.recorded_date.desc()).first()
    if latest:
        print(f'Latest entry: {latest.recorded_date} - {latest.weight_lbs} lbs, {latest.body_fat_percentage}%')
"
```

**Test in browser:**
1. Login to https://bowmanhomelabtech.net
2. Navigate to Health & Fitness → Health Metrics Log
3. You should see your imported data displayed in a table

---

### Step 6: Set Up Automated Database Backups

Configure daily automated backups:

```bash
# SSH into your server
ssh nathan@your-server-ip

cd /home/nathan/vitruvian-developer

# Make backup script executable (if not already)
chmod +x scripts/backup-database.sh

# Test the backup script manually
sudo ./scripts/backup-database.sh
```

**Expected output:**
```
[INFO] ======================================
[INFO] PostgreSQL Backup - Mon Dec 16 14:30:00 UTC 2024
[INFO] ======================================
[INFO] Creating database backup...
[INFO] Backup created successfully: primary_assistant_backup_20241216_143000.sql.gz (1.2M)
[INFO] Verifying backup integrity...
[INFO] Backup integrity verified
[INFO] Current backup count: 1
[INFO] ======================================
[INFO] Backup complete!
[INFO] ======================================
```

**Set up automatic daily backups:**

```bash
# Edit crontab as root
sudo crontab -e

# Add this line to run backups daily at 2 AM:
0 2 * * * /home/nathan/vitruvian-developer/scripts/backup-database.sh >> /var/log/primary-assistant-backup.log 2>&1

# Save and exit (Ctrl+X, Y, Enter)

# Verify crontab was added
sudo crontab -l
```

**Backup configuration:**
- **Location:** `/home/nathan/backups/primary-assistant/`
- **Frequency:** Daily at 2:00 AM
- **Retention:** 30 days (automatically deletes older backups)
- **Format:** Compressed SQL dumps (`.sql.gz`)
- **Logs:** `/var/log/primary-assistant-backup.log`

**View backups:**

```bash
# List all backups
ls -lh /home/nathan/backups/primary-assistant/

# Check backup log
tail -f /var/log/primary-assistant-backup.log
```

**Restore from backup (if needed):**

```bash
# Stop the application
cd /home/nathan/vitruvian-developer
docker-compose down

# Restore from a specific backup
gunzip < /home/nathan/backups/primary-assistant/primary_assistant_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker-compose exec -T db psql -U postgres -d primary_assistant

# Start the application
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d
```

---

## ✅ Post-Deployment Verification

After completing all steps, verify everything is working:

### 1. HTTPS & Domain
- [ ] `https://bowmanhomelabtech.net` loads with valid SSL certificate
- [ ] `http://bowmanhomelabtech.net` redirects to HTTPS
- [ ] `https://www.bowmanhomelabtech.net` works
- [ ] SSL Labs rating is A or A+

### 2. Application Functionality
- [ ] Login works at `https://bowmanhomelabtech.net/auth/login`
- [ ] All static files load correctly (CSS, JS, images)
- [ ] Project navigation works
- [ ] Blog posts load correctly

### 3. Virtual Database Pages (when logged in)
- [ ] Health Metrics Log displays imported data
- [ ] Workout Log is accessible (may be empty)
- [ ] Meal Log is accessible (may be empty)
- [ ] Progress Photos is accessible (may be empty)
- [ ] Coaching Sessions is accessible (may be empty)

### 4. Backups
- [ ] Initial manual backup completed successfully
- [ ] Backup files exist in `/home/nathan/backups/primary-assistant/`
- [ ] Cron job is scheduled: `sudo crontab -l`

### 5. Security
- [ ] SESSION_COOKIE_SECURE is enabled (cookies only sent over HTTPS)
- [ ] HSTS header is present: `curl -I https://bowmanhomelabtech.net | grep Strict-Transport-Security`
- [ ] Certificate auto-renewal is configured: `sudo crontab -l | grep certbot`

---

## 🔧 Troubleshooting

### SSL Certificate Issues

**Problem:** `Certificate not found` error

**Solution:**
```bash
# Check if certificates exist
sudo ls -la /etc/letsencrypt/live/bowmanhomelabtech.net/

# If missing, obtain manually
sudo certbot certonly --standalone \
  -d bowmanhomelabtech.net \
  -d www.bowmanhomelabtech.net

# Restart nginx
cd /home/nathan/vitruvian-developer
docker-compose restart nginx
```

**Problem:** Certificate renewal fails

**Solution:**
```bash
# Test renewal manually
sudo certbot renew --dry-run

# Check nginx is allowing ACME challenges
curl http://bowmanhomelabtech.net/.well-known/acme-challenge/test
# Should return 404, not a redirect
```

### Container Issues

**Problem:** Nginx won't start after HTTPS config

**Solution:**
```bash
# Check nginx logs
docker-compose logs nginx

# Common issue: SSL files not mounted
# Verify volumes in docker-compose.yml

# Temporarily use HTTP-only config to debug
docker-compose -f docker-compose.yml up -d
```

### Import Issues

**Problem:** Health data import fails

**Solution:**
```bash
# Check file format
head -20 check-in-log.md

# Verify table format matches:
# | Date | Weight (lbs) | Body Fat % | Notes |

# Check database connectivity
docker-compose exec web python -c "from website import create_app, db; app = create_app(); app.app_context().push(); print('DB Connected')"
```

### Backup Issues

**Problem:** Backups not running

**Solution:**
```bash
# Check cron is running
sudo systemctl status cron

# Check cron logs
sudo grep CRON /var/log/syslog | tail -20

# Test backup script manually
sudo /home/nathan/vitruvian-developer/scripts/backup-database.sh

# Check permissions
ls -la /home/nathan/vitruvian-developer/scripts/backup-database.sh
# Should be executable (-rwxr-xr-x)
```

---

## 📚 Additional Resources

### Certificate Management
- **View certificate details:** `sudo certbot certificates`
- **Test renewal:** `sudo certbot renew --dry-run`
- **Force renewal:** `sudo certbot renew --force-renewal`
- **Revoke certificate:** `sudo certbot revoke --cert-path /etc/letsencrypt/live/bowmanhomelabtech.net/cert.pem`

### Container Management
- **View all logs:** `docker-compose logs`
- **Follow logs:** `docker-compose logs -f web`
- **Restart service:** `docker-compose restart web`
- **Rebuild:** `docker-compose up -d --build`
- **Check status:** `docker-compose ps`

### Database Management
- **Access PostgreSQL:** `docker-compose exec db psql -U postgres -d primary_assistant`
- **List tables:** `\dt`
- **Count records:** `SELECT COUNT(*) FROM health_metrics;`
- **View recent entries:** `SELECT * FROM health_metrics ORDER BY recorded_date DESC LIMIT 10;`

---

## 🎉 Success Criteria

Your production deployment is complete when:

1. ✅ **HTTPS is working** - Site loads at https://bowmanhomelabtech.net with valid certificate
2. ✅ **Authentication works** - Can login and access protected pages
3. ✅ **Health data imported** - Health Metrics Log shows your historical data
4. ✅ **Backups configured** - Daily automated backups running successfully
5. ✅ **Auto-renewal working** - Certbot cron job configured for certificate renewal

---

## 🚀 Next Steps (Optional Enhancements)

After successful deployment, consider:

1. **Custom Domain Email** - Set up email for contact form
2. **Monitoring** - Add uptime monitoring (UptimeRobot, Pingdom)
3. **Analytics** - Add privacy-focused analytics (Plausible, Fathom)
4. **CDN** - Configure Cloudflare for additional performance/security
5. **Email Notifications** - Get backup failure alerts via email/webhook
6. **Additional Data Import** - Import workout logs, meal logs, etc.
7. **Database Replication** - Set up read replicas for high availability
8. **Docker Secrets** - Move passwords to Docker secrets instead of .env

---

## 📞 Support & Documentation

- **CLAUDE.md** - Project documentation and commands
- **SESSION_NOTES.md** - Session history and troubleshooting
- **DOCKER_README.md** - Docker configuration details
- **docs/database/** - Database schema and design
- **GitHub Issues** - Report bugs or request features

---

*Generated on: December 16, 2024*
*Domain: bowmanhomelabtech.net*
*Server: Ubuntu 24.04 LTS*
