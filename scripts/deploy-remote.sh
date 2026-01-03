#!/bin/bash
#
# Remote Deployment Script for Vitruvian Developer
# Usage: ./scripts/deploy-remote.sh
#

set -e  # Exit on error

echo "🚀 Starting deployment to remote server..."
echo ""

# Step 1: Commit and push changes
echo "📦 Step 1: Pushing local changes to GitHub..."
git add -A
git status --short
read -p "Enter commit message (or press Enter to skip commit): " commit_msg
if [ -n "$commit_msg" ]; then
    git commit -m "$commit_msg"
    git push origin main
    echo "✅ Changes pushed to GitHub"
else
    echo "⏭️  Skipping commit (using existing commits)"
fi
echo ""

# Step 2: Pull on remote server
echo "📥 Step 2: Pulling latest code on remote server..."
sshpass -p "Serbatik11!!" ssh -o StrictHostKeyChecking=no nathan@vit-dev-website \
    "cd /home/nathan/vitruvian-developer && git pull origin main"
echo "✅ Code updated on remote server"
echo ""

# Step 3: Rebuild and restart containers
echo "🔨 Step 3: Rebuilding Docker containers..."
sshpass -p "Serbatik11!!" ssh -o StrictHostKeyChecking=no nathan@vit-dev-website \
    "cd /home/nathan/vitruvian-developer && \
     docker-compose -f docker-compose.yml -f docker-compose.remote.yml stop web && \
     docker-compose -f docker-compose.yml -f docker-compose.remote.yml rm -f web && \
     docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d --build web"
echo "✅ Containers rebuilt and started"
echo ""

# Step 4: Wait for health check
echo "⏳ Step 4: Waiting for application to be healthy..."
sleep 15
sshpass -p "Serbatik11!!" ssh -o StrictHostKeyChecking=no nathan@vit-dev-website \
    "cd /home/nathan/vitruvian-developer && docker-compose -f docker-compose.yml -f docker-compose.remote.yml ps web"
echo ""

# Step 5: Check if nginx needs reload
echo "🔄 Step 5: Checking nginx configuration..."
if git diff HEAD~1 --name-only | grep -q "docker/nginx"; then
    echo "📝 Nginx config changed, reloading..."
    sshpass -p "Serbatik11!!" ssh -o StrictHostKeyChecking=no nathan@vit-dev-website \
        "cd /home/nathan/vitruvian-developer && \
         docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T nginx nginx -s reload"
    echo "✅ Nginx reloaded"
else
    echo "⏭️  No nginx changes detected"
fi
echo ""

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Test the application: https://vitruvian.bowmanhomelabtech.net"
echo "   2. If JavaScript changed: Purge Cloudflare cache or enable Development Mode"
echo "   3. Check logs: docker-compose logs -f web"
echo ""
