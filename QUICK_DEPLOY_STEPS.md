# Quick Deployment Steps for bowmanhomelabtech.net

## 🎯 Current Status
- ✅ Code pushed to GitHub
- ✅ HTTPS configuration ready
- ✅ Scripts created and tested
- ⏳ Awaiting deployment to server

---

## 📝 Run These Commands on Remote Server

### 1. Pull Latest Code
```bash
ssh nathan@your-server-ip
cd /home/nathan/vitruvian-developer
git pull origin main
```

### 2. Set Up HTTPS (Automated)
```bash
sudo ./scripts/setup-ssl.sh
```
*Takes 2-3 minutes. Obtains SSL certificate and configures HTTPS.*

### 3. Test HTTPS
```bash
curl -I https://bowmanhomelabtech.net
# Should see: HTTP/2 200

# Test in browser:
# https://bowmanhomelabtech.net
```

### 4. Import Health Data
```bash
# First, copy your local file to server
# (Run from LOCAL machine):
scp ~/primary-assistant/Health_and_Fitness/data/check-in-log.md nathan@your-server-ip:/home/nathan/

# Then on server:
docker-compose exec web python scripts/import-health-data.py /home/nathan/check-in-log.md
```

### 5. Set Up Daily Backups
```bash
# Test backup manually
sudo ./scripts/backup-database.sh

# Add to crontab
sudo crontab -e
# Add this line:
0 2 * * * /home/nathan/vitruvian-developer/scripts/backup-database.sh >> /var/log/primary-assistant-backup.log 2>&1
```

---

## ✅ Verification Checklist

After deployment:

- [ ] Visit https://bowmanhomelabtech.net (see lock icon)
- [ ] Login works
- [ ] Health Metrics Log shows imported data
- [ ] Check SSL rating: https://www.ssllabs.com/ssltest/
- [ ] Verify backup exists: `ls /home/nathan/backups/primary-assistant/`
- [ ] Check cron job: `sudo crontab -l`

---

## 🆘 If Something Goes Wrong

**Container won't start:**
```bash
docker-compose logs nginx
docker-compose logs web
```

**SSL issues:**
```bash
sudo ls /etc/letsencrypt/live/bowmanhomelabtech.net/
sudo certbot renew --dry-run
```

**Need HTTP only temporarily:**
```bash
docker-compose -f docker-compose.yml up -d
# (Skips the remote.yml override)
```

---

## 📚 Full Documentation

See `docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md` for complete instructions, troubleshooting, and explanations.
