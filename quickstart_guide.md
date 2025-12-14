# Server Deployment Quick Start Guide

**Best method for deploying the Primary Assistant website application to a server**

## ✅ Recommended: Docker Deployment via Git Clone

**Yes, installing git and cloning the repo is the standard and recommended approach.** Here's why and how:

### Best Practice Deployment Flow

```bash
# 1. On your server, install prerequisites
sudo apt update
sudo apt install -y git docker.io docker-compose

# 2. Clone the repository
git clone https://github.com/nbowman189/primary-assistant.git
cd primary-assistant

# 3. Set up environment
cp .env.example .env
nano .env  # Configure SECRET_KEY, POSTGRES_PASSWORD, etc.

# 4. Deploy with Docker
docker-compose up -d

# 5. Initialize database
docker-compose exec web flask db upgrade
docker-compose exec web flask create-admin
```

**Done!** Your application is running with Nginx on ports 80/443.

---

## 🐳 Why Docker Deployment is Best for This Project

You already have a **production-ready Docker setup** that includes:

✅ **Automated setup** - Everything configured in docker-compose.yml
✅ **Consistency** - Same environment everywhere (dev, staging, prod)
✅ **Isolation** - Services containerized with proper networking
✅ **Security** - Non-root users, internal networks, rate limiting
✅ **Easy updates** - `git pull && docker-compose up -d --build`
✅ **Rollback capability** - Easy to revert via git commits
✅ **Built-in monitoring** - Health checks on all services

---

## 📋 Deployment Methods Comparison

### 1. **Docker via Git Clone** (⭐ Recommended)

**Pros:**
- Simplest production deployment
- Your entire setup is already Docker-ready
- One-command deployment
- Easy scaling and updates
- Nginx, PostgreSQL, Flask all configured

**Cons:**
- Requires Docker on server (easy to install)
- Slightly more resource overhead than bare metal

**Best for:** Production deployments, most server environments

---

### 2. **Git Clone + Manual Setup** (Traditional)

```bash
git clone https://github.com/nbowman189/primary-assistant.git
cd primary-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r website/requirements.txt
# Install PostgreSQL manually
# Configure nginx manually
# Set up systemd services manually
```

**Pros:**
- More granular control
- Slightly less resource usage
- Familiar to traditional sysadmins

**Cons:**
- Much more manual configuration
- Environment inconsistencies
- Manual dependency management
- More prone to errors
- Harder to replicate

**Best for:** Shared hosting without Docker support, specific customization needs

---

### 3. **CI/CD Pipeline** (Advanced)

GitHub Actions → Build → Deploy to server automatically on push

**Pros:**
- Fully automated
- Consistent deployments
- Automatic testing before deploy
- Professional workflow

**Cons:**
- Requires initial setup time
- Overkill for single-person projects
- Needs secrets management

**Best for:** Team projects, frequent deployments, production-critical apps

---

## 🚀 Step-by-Step: Docker Deployment (Recommended)

### Prerequisites on Server

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y git docker.io docker-compose

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add your user to docker group (optional, to avoid sudo)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

### Deployment Steps

```bash
# 1. Clone repository
cd /opt  # or wherever you want the app
sudo git clone https://github.com/nbowman189/primary-assistant.git
cd primary-assistant

# 2. Configure environment
sudo cp .env.example .env
sudo nano .env

# Required settings in .env:
# SECRET_KEY=<generate with: python scripts/generate_secret_key.py>
# POSTGRES_PASSWORD=<secure-password>
# POSTGRES_DB=fitness_db
# POSTGRES_USER=fitness_user
# FLASK_ENV=production
# FLASK_DEBUG=False

# 3. Generate secret key
python3 scripts/generate_secret_key.py
# Copy output to .env

# 4. Start services
sudo docker-compose up -d

# 5. Check services are running
sudo docker-compose ps
# All should show "Up (healthy)"

# 6. Initialize database
sudo docker-compose exec web flask db upgrade

# 7. Create admin user
sudo docker-compose exec web flask create-admin
# Follow prompts

# 8. Verify deployment
curl http://localhost/health
# Should return 200 OK
```

### Configure SSL (Optional but Recommended)

```bash
# 1. Install certbot
sudo apt install -y certbot python3-certbot-nginx

# 2. Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# 3. Update docker/nginx/nginx.conf with SSL settings
# (Template included in file, uncomment SSL section)

# 4. Rebuild and restart
sudo docker-compose up -d --build
```

---

## 🔄 Updates & Maintenance

### Update Application

```bash
cd /opt/primary-assistant
sudo git pull
sudo docker-compose up -d --build  # Rebuild and restart
```

### View Logs

```bash
# All services
sudo docker-compose logs -f

# Specific service
sudo docker-compose logs -f web
sudo docker-compose logs -f db
sudo docker-compose logs -f nginx
```

### Backup Database

```bash
# Backup
sudo docker-compose exec db pg_dump -U fitness_user fitness_db > backup_$(date +%Y%m%d).sql

# Restore
sudo docker-compose exec -T db psql -U fitness_user fitness_db < backup_20241214.sql
```

### Restart Services

```bash
# Restart all services
sudo docker-compose restart

# Restart specific service
sudo docker-compose restart web
sudo docker-compose restart nginx
```

### Stop Services

```bash
# Stop all services (preserves data)
sudo docker-compose down

# Stop and remove volumes (⚠️ DELETES ALL DATA)
sudo docker-compose down -v
```

---

## 🔧 Troubleshooting

### Services Won't Start

```bash
# Check logs
sudo docker-compose logs

# Verify environment variables
cat .env

# Check ports are available
sudo netstat -tlnp | grep -E '(80|443|5432|8000)'
```

### Database Connection Issues

```bash
# Check database is healthy
sudo docker-compose ps db

# Test database connection
sudo docker-compose exec db psql -U fitness_user -d fitness_db

# Reinitialize database
sudo docker-compose down
sudo docker-compose up -d
sudo docker-compose exec web flask db upgrade
```

### 502 Bad Gateway

```bash
# Check Flask app is running
sudo docker-compose logs web

# Verify health endpoint
sudo docker-compose exec web curl http://localhost:8000/health

# Restart web service
sudo docker-compose restart web
```

### Permission Errors

```bash
# Fix ownership of project directory
sudo chown -R $USER:$USER /opt/primary-assistant

# Fix log directory permissions
sudo mkdir -p /opt/primary-assistant/logs
sudo chmod 755 /opt/primary-assistant/logs
```

---

## 📚 Related Documentation

You already have comprehensive guides in the repository:

- **`DOCKER_README.md`** - Complete Docker implementation guide
- **`website/DEPLOYMENT_GUIDE.md`** - Detailed deployment procedures and options
- **`website/CONFIGURATION_GUIDE.md`** - Configuration details and environment variables
- **`README.md`** - Project overview and quick start commands
- **`.env.example`** - Environment variable template with detailed comments

---

## 🎯 Recommendation Summary

**Use Docker deployment via git clone.**

Here's why it's perfect for your project:

1. ✅ You've already done all the Docker work
2. ✅ Production-ready configuration exists
3. ✅ Simple deployment: clone + docker-compose up
4. ✅ Easy to maintain and update
5. ✅ Consistent environment everywhere
6. ✅ Professional setup with Nginx, PostgreSQL, security

The git clone approach gives you version control benefits (rollback, branching) combined with Docker's deployment simplicity.

---

## 🔐 Security Checklist

Before going to production:

- [ ] Generate strong `SECRET_KEY` (use `scripts/generate_secret_key.py`)
- [ ] Set secure `POSTGRES_PASSWORD`
- [ ] Set `FLASK_ENV=production` and `FLASK_DEBUG=False`
- [ ] Configure SSL certificates for HTTPS
- [ ] Review rate limiting settings in `docker/nginx/nginx.conf`
- [ ] Set up automated database backups
- [ ] Configure log rotation
- [ ] Set up monitoring and alerts
- [ ] Review security headers in nginx config
- [ ] Verify firewall rules (allow 80, 443; block 5432, 8000)
- [ ] Test health check endpoints
- [ ] Create admin user with strong password
- [ ] Review and update `.env` file permissions (should be 600)

---

## 🌐 Firewall Configuration

```bash
# If using UFW (Ubuntu)
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH (if needed)
sudo ufw enable

# Verify rules
sudo ufw status
```

---

## 📊 Monitoring

### Check Service Health

```bash
# All services status
sudo docker-compose ps

# Application health endpoint
curl http://localhost/health

# Database health
sudo docker-compose exec db pg_isready -U fitness_user
```

### Resource Usage

```bash
# Container stats
sudo docker stats

# Disk usage
sudo docker system df
```

---

**Last Updated**: December 14, 2024
**Deployment Method**: Docker Compose via Git Clone
**Status**: Production-Ready
