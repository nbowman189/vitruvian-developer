# Vitruvian Developer - Deployment Quick Start Guide

**Streamlined Docker deployment for Ubuntu/Debian servers**

---

## 🚀 Automated Setup Script (Recommended)

Save and run this script for automated deployment:

```bash
#!/bin/bash
# Vitruvian Developer - Automated Docker Deployment Script
# Run with: bash deploy.sh

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       Vitruvian Developer - Automated Deployment             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run as root. Run as regular user with sudo access."
    exit 1
fi

# Step 1: Install prerequisites
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Installing prerequisites..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sudo apt update
sudo apt install -y git docker.io docker-compose-plugin curl

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group (optional - requires re-login)
if ! groups $USER | grep -q docker; then
    sudo usermod -aG docker $USER
    print_warning "Added $USER to docker group. You'll need to log out and back in for this to take effect."
    print_warning "After re-login, re-run this script."
    exit 0
fi

print_status "Prerequisites installed"
echo ""

# Step 2: Clone repository
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Cloning repository..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

INSTALL_DIR="/opt/vitruvian-developer"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "Directory $INSTALL_DIR already exists"
    read -p "Pull latest changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd $INSTALL_DIR
        git pull
        print_status "Repository updated"
    fi
else
    sudo git clone https://github.com/nbowman189/vitruvian-developer.git $INSTALL_DIR
    sudo chown -R $USER:$USER $INSTALL_DIR
    print_status "Repository cloned to $INSTALL_DIR"
fi

cd $INSTALL_DIR
echo ""

# Step 3: Configure environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Configuring environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f .env ]; then
    cp .env.example .env
    print_status ".env file created"

    # Generate SECRET_KEY
    if command -v python3 &> /dev/null; then
        SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        sed -i "s|SECRET_KEY=your-secret-key-here-generate-with-script|SECRET_KEY=$SECRET_KEY|g" .env
        print_status "SECRET_KEY generated and set"
    else
        print_warning "Python3 not found. You'll need to set SECRET_KEY manually."
    fi

    # Prompt for database password
    echo ""
    read -sp "Enter a secure PostgreSQL password: " DB_PASSWORD
    echo
    sed -i "s|POSTGRES_PASSWORD=your-secure-database-password-here|POSTGRES_PASSWORD=$DB_PASSWORD|g" .env
    print_status "POSTGRES_PASSWORD set"

    # Set production environment
    sed -i "s|FLASK_ENV=development|FLASK_ENV=production|g" .env
    sed -i "s|FLASK_DEBUG=true|FLASK_DEBUG=false|g" .env
    print_status "Production environment configured"
else
    print_warning ".env file already exists, skipping configuration"
fi

# Secure .env file
chmod 600 .env
print_status ".env file secured (chmod 600)"
echo ""

# Step 4: Clean up old containers (if any)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Cleaning up old containers..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Use docker compose v2 (no hyphen) to avoid ContainerConfig bug
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    print_status "Using Docker Compose V2"
else
    DOCKER_COMPOSE="docker-compose"
    print_warning "Using older docker-compose. Consider upgrading to V2."
fi

# Stop and remove old containers
$DOCKER_COMPOSE down -v --remove-orphans 2>/dev/null || true
docker rm -f primary-assistant-db primary-assistant-web primary-assistant-nginx 2>/dev/null || true

print_status "Old containers removed"
echo ""

# Step 5: Build and start services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Building and starting services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

$DOCKER_COMPOSE build --no-cache
print_status "Docker images built"

$DOCKER_COMPOSE up -d
print_status "Services started"
echo ""

# Step 6: Wait for services to be healthy
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Waiting for services to be healthy..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Wait up to 120 seconds for all services to be healthy
TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    UNHEALTHY=$($DOCKER_COMPOSE ps | grep -c "unhealthy" || true)
    STARTING=$($DOCKER_COMPOSE ps | grep -c "starting" || true)

    if [ $UNHEALTHY -eq 0 ] && [ $STARTING -eq 0 ]; then
        print_status "All services are healthy!"
        break
    fi

    echo -n "."
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

echo ""

if [ $ELAPSED -ge $TIMEOUT ]; then
    print_error "Services did not become healthy within ${TIMEOUT}s"
    echo ""
    echo "Container status:"
    $DOCKER_COMPOSE ps
    echo ""
    echo "Check logs with: $DOCKER_COMPOSE logs"
    exit 1
fi

echo ""

# Step 7: Verify deployment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Verifying deployment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check container status
echo "Container status:"
$DOCKER_COMPOSE ps
echo ""

# Test health endpoint
if curl -f http://localhost/api/health &> /dev/null; then
    print_status "Health endpoint responding"
else
    print_error "Health endpoint not responding"
    echo "Run: curl http://localhost/api/health"
fi

# Test homepage
if curl -f http://localhost/ &> /dev/null; then
    print_status "Homepage accessible"
else
    print_error "Homepage not accessible"
fi

echo ""

# Step 8: Summary
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  Deployment Complete!                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Services:"
echo "   • PostgreSQL: Running (internal only)"
echo "   • Flask Web:  Running on port 8000 (internal)"
echo "   • Nginx:      Running on ports 80/443"
echo ""
echo "🌐 Access your application:"
echo "   • HTTP:   http://localhost/"
echo "   • Health: http://localhost/api/health"
echo ""
echo "📝 Useful commands:"
echo "   • View logs:    $DOCKER_COMPOSE logs -f"
echo "   • Stop:         $DOCKER_COMPOSE down"
echo "   • Restart:      $DOCKER_COMPOSE restart"
echo "   • Status:       $DOCKER_COMPOSE ps"
echo ""
echo "📖 Documentation: $INSTALL_DIR/DOCKER_README.md"
echo ""
echo "🔐 Next steps:"
echo "   • Configure firewall (allow ports 80, 443)"
echo "   • Set up SSL certificates"
echo "   • Configure domain name"
echo ""
```

**Save this as `deploy.sh` and run:**
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📋 Manual Deployment Steps

If you prefer manual deployment or need to troubleshoot:

### Step 1: Install Prerequisites

```bash
# Update system
sudo apt update

# Install required packages
sudo apt install -y git docker.io docker-compose-plugin curl

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group (optional - requires logout/login)
sudo usermod -aG docker $USER
```

**⚠️ Important**: After adding user to docker group, log out and back in.

### Step 2: Clone Repository

```bash
# Clone to /opt (recommended for production)
sudo git clone https://github.com/nbowman189/vitruvian-developer.git /opt/vitruvian-developer

# Change ownership to your user
sudo chown -R $USER:$USER /opt/vitruvian-developer

# Navigate to directory
cd /opt/vitruvian-developer
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate SECRET_KEY
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'

# Edit .env file
nano .env
```

**Required `.env` values**:
```bash
# Generated secret key
SECRET_KEY=<paste-generated-key-here>

# Strong database password
POSTGRES_PASSWORD=<your-secure-password>

# Database settings (must match docker-compose.yml)
POSTGRES_USER=postgres
POSTGRES_DB=primary_assistant
POSTGRES_HOST=db

# Production settings
FLASK_ENV=production
FLASK_DEBUG=false
```

**Secure the file**:
```bash
chmod 600 .env
```

### Step 4: Clean Previous Deployment (If Any)

```bash
# Stop old containers
docker compose down -v --remove-orphans

# Remove old containers (if stuck)
docker rm -f primary-assistant-db primary-assistant-web primary-assistant-nginx

# Clean Docker cache (if needed)
docker system prune -f
```

### Step 5: Build and Deploy

```bash
# Build images (no cache for fresh build)
docker compose build --no-cache

# Start services in detached mode
docker compose up -d

# Monitor logs during startup
docker compose logs -f
```

**Press Ctrl+C to exit logs**

### Step 6: Verify Deployment

```bash
# Check container status (all should be "Up (healthy)")
docker compose ps

# Test health endpoint
curl http://localhost/api/health
# Expected: {"status":"healthy","service":"vitruvian-developer"}

# Test homepage
curl http://localhost/
# Should return HTML

# Check logs if issues
docker compose logs web
docker compose logs nginx
docker compose logs db
```

---

## 🔧 Common Issues & Solutions

### Issue 1: "ContainerConfig" KeyError

**Cause**: Old docker-compose version (1.29.2) has a caching bug

**Solution**: Use Docker Compose V2 (no hyphen)
```bash
# Install V2
sudo apt install docker-compose-plugin

# Use new command (no hyphen)
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Issue 2: Containers Not Healthy

**Check which container**:
```bash
docker compose ps
```

**If db is unhealthy**:
```bash
docker compose logs db
# Check for password/configuration issues
```

**If web is unhealthy**:
```bash
docker compose logs web
# Check .env file has correct SECRET_KEY and POSTGRES_PASSWORD
# Verify values are not placeholders
```

**If nginx is unhealthy**:
```bash
# Check if web is healthy first
docker compose ps web

# Check nginx logs
docker compose logs nginx

# Test web directly
docker compose exec web curl http://localhost:8000/api/health
```

### Issue 3: Port Already in Use

```bash
# Check what's using port 80
sudo lsof -i :80

# Check what's using port 443
sudo lsof -i :443

# Stop conflicting service (e.g., Apache)
sudo systemctl stop apache2
sudo systemctl disable apache2
```

### Issue 4: Permission Denied

```bash
# Ensure user is in docker group
groups $USER | grep docker

# If not, add and re-login
sudo usermod -aG docker $USER
# Then logout and login again

# Fix directory permissions
sudo chown -R $USER:$USER /opt/vitruvian-developer
```

### Issue 5: Cannot Connect to Docker Daemon

```bash
# Check Docker is running
sudo systemctl status docker

# Start Docker
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker
```

---

## 🔄 Updates & Maintenance

### Update Application

```bash
cd /opt/vitruvian-developer

# Pull latest code
git pull

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Verify
docker compose ps
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f nginx
docker compose logs -f db

# Last 100 lines
docker compose logs --tail=100 web
```

### Backup Database

```bash
# Create backup
docker compose exec db pg_dump -U postgres primary_assistant > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker compose exec -T db psql -U postgres primary_assistant < backup_20241214_120000.sql
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart web
docker compose restart nginx
```

### Stop Services

```bash
# Stop (preserves data)
docker compose down

# Stop and remove volumes (⚠️ DELETES DATA)
docker compose down -v
```

---

## 🔐 Security Checklist

Before production use:

- [ ] Set strong `SECRET_KEY` (generated, not placeholder)
- [ ] Set secure `POSTGRES_PASSWORD` (strong password)
- [ ] `.env` file permissions set to 600
- [ ] `FLASK_ENV=production` and `FLASK_DEBUG=false`
- [ ] Firewall configured (allow 80, 443; block 5432, 8000)
- [ ] SSL certificates installed (see SSL section below)
- [ ] Domain name configured
- [ ] Backups automated
- [ ] Monitoring set up

---

## 🌐 SSL Configuration (HTTPS)

### Option 1: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install -y certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in: /etc/letsencrypt/live/yourdomain.com/

# Copy to project
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/key.pem

# Update nginx config
nano docker/nginx/nginx.conf
# Uncomment SSL section and update server_name

# Restart nginx
docker compose restart nginx
```

### Option 2: Self-Signed Certificate (Development)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/key.pem \
  -out docker/nginx/ssl/cert.pem

# Restart nginx
docker compose restart nginx
```

---

## 🌐 Firewall Configuration

### Using UFW (Ubuntu)

```bash
# Install UFW
sudo apt install ufw

# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Using iptables

```bash
# Allow HTTP
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# Allow HTTPS
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Save rules
sudo netfilter-persistent save
```

---

## 📊 Monitoring

### Check Service Health

```bash
# Container status
docker compose ps

# Health endpoint
curl http://localhost/api/health

# Database health
docker compose exec db pg_isready -U postgres
```

### Resource Usage

```bash
# Container resource usage
docker stats

# Docker disk usage
docker system df

# Server resources
htop  # Install with: sudo apt install htop
```

---

## 📚 Related Documentation

- **Complete Docker Guide**: `/DOCKER_README.md`
- **Docker Issues & Fixes**: `/docs/docker/`
- **Deployment Guide**: `/website/DEPLOYMENT_GUIDE.md`
- **Configuration Guide**: `/website/CONFIGURATION_GUIDE.md`
- **Troubleshooting**: `/docs/docker/TROUBLESHOOTING.md`

---

## 🎯 Quick Reference

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# View logs
docker compose logs -f

# Check status
docker compose ps

# Restart a service
docker compose restart web

# Update application
git pull && docker compose up -d --build

# Clean restart
docker compose down -v && docker compose up -d --build
```

---

**Last Updated**: December 14, 2024
**Repository**: https://github.com/nbowman189/vitruvian-developer
**Status**: Production-Ready with automated deployment script
