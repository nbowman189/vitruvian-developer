#!/bin/bash
# Setup SSL certificates with Let's Encrypt for bowmanhomelabtech.net
# Run this script on your remote server after DNS is configured

set -e  # Exit on error

echo "======================================"
echo "SSL Certificate Setup for bowmanhomelabtech.net"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root or with sudo"
    exit 1
fi

# Variables
DOMAIN="bowmanhomelabtech.net"
EMAIL="nbowman189@gmail.com"  # For Let's Encrypt notifications

echo "🔍 Step 1: Installing Certbot..."
# Install Certbot
if ! command -v certbot &> /dev/null; then
    apt-get update
    apt-get install -y certbot
    echo "✅ Certbot installed"
else
    echo "✅ Certbot already installed"
fi

echo ""
echo "🔍 Step 2: Creating required directories..."
# Create directories for certbot
mkdir -p /var/www/certbot
mkdir -p /etc/letsencrypt
echo "✅ Directories created"

echo ""
echo "🔍 Step 3: Checking DNS configuration..."
# Check if domain resolves to this server
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)

echo "Server IP: $SERVER_IP"
echo "Domain resolves to: $DOMAIN_IP"

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    echo "⚠️  WARNING: Domain does not resolve to this server yet!"
    echo "   DNS propagation may still be in progress."
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted. Please wait for DNS to propagate and try again."
        exit 1
    fi
fi

echo ""
echo "🔍 Step 4: Temporarily modifying nginx config for HTTP verification..."
# We need to temporarily allow HTTP access for the ACME challenge
cd /home/nathan/vitruvian-developer

# Create a temporary nginx config that only handles HTTP
cat > docker/nginx/nginx.conf.temp << 'EOF'
upstream flask_app {
    server web:8000;
}

server {
    listen 80;
    server_name bowmanhomelabtech.net www.bowmanhomelabtech.net;

    # Allow Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Temporarily allow all traffic (for initial setup)
    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Backup original config and use temp
cp docker/nginx/nginx.conf docker/nginx/nginx.conf.backup
cp docker/nginx/nginx.conf.temp docker/nginx/nginx.conf

echo "✅ Temporary config created"

echo ""
echo "🔍 Step 5: Restarting nginx with temporary config..."
docker-compose restart nginx
sleep 5
echo "✅ Nginx restarted"

echo ""
echo "🔍 Step 6: Obtaining SSL certificate from Let's Encrypt..."
# Obtain certificate using standalone mode
certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d $DOMAIN \
    -d www.$DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully!"
else
    echo "❌ Failed to obtain SSL certificate"
    echo "   Restoring original nginx config..."
    cp docker/nginx/nginx.conf.backup docker/nginx/nginx.conf
    docker-compose restart nginx
    exit 1
fi

echo ""
echo "🔍 Step 7: Restoring production nginx config..."
# Restore the full HTTPS config
cp docker/nginx/nginx.conf.backup docker/nginx/nginx.conf

echo ""
echo "🔍 Step 8: Rebuilding and restarting containers with HTTPS..."
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d --build nginx

echo ""
echo "🔍 Step 9: Setting up automatic certificate renewal..."
# Add cron job for renewal
CRON_JOB="0 3 * * * certbot renew --quiet --post-hook 'docker-compose -C /home/nathan/vitruvian-developer restart nginx'"
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$CRON_JOB") | crontab -
echo "✅ Certificate auto-renewal configured (daily at 3 AM)"

echo ""
echo "======================================"
echo "✅ SSL Setup Complete!"
echo "======================================"
echo ""
echo "Your site is now accessible at:"
echo "  🌐 https://bowmanhomelabtech.net"
echo "  🌐 https://www.bowmanhomelabtech.net"
echo ""
echo "Certificate details:"
echo "  📁 Location: /etc/letsencrypt/live/$DOMAIN/"
echo "  📅 Expires: $(date -d "+90 days" +%Y-%m-%d) (auto-renews)"
echo ""
echo "Next steps:"
echo "  1. Test HTTPS: curl -I https://bowmanhomelabtech.net"
echo "  2. Check SSL rating: https://www.ssllabs.com/ssltest/"
echo "  3. Update any bookmarks to use HTTPS"
echo ""
