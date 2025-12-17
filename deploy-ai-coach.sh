#!/bin/bash
# AI Coach Deployment Script for Remote Server
# This script deploys the AI Coach feature with all fixes applied

set -e  # Exit on any error

echo "========================================="
echo "AI Coach Deployment Script"
echo "========================================="
echo ""

# Navigate to project directory
cd /home/nathan/vitruvian-developer

echo "Step 1: Pull latest changes from GitHub..."
git pull
echo "✓ Code updated"
echo ""

echo "Step 2: Stop and remove web container..."
docker-compose -f docker-compose.yml -f docker-compose.remote.yml stop web
docker-compose -f docker-compose.yml -f docker-compose.remote.yml rm -f web
echo "✓ Web container removed"
echo ""

echo "Step 3: Rebuild and start web container..."
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d --build web
echo "✓ Web container rebuilt"
echo ""

echo "Step 4: Waiting for web container to be healthy (30 seconds)..."
sleep 30
echo ""

echo "Step 5: Verifying deployment..."
echo ""

# Check container status
echo "Container status:"
docker-compose ps web
echo ""

# Verify GEMINI_API_KEY is set
echo "Checking GEMINI_API_KEY..."
if docker-compose exec web env | grep -q "GEMINI_API_KEY="; then
    echo "✓ GEMINI_API_KEY is set"
else
    echo "✗ GEMINI_API_KEY is NOT set - AI Coach will not work!"
    exit 1
fi
echo ""

# Verify routes are registered
echo "Checking AI Coach routes..."
ROUTE_COUNT=$(docker-compose exec web python -c "from website import create_app; app = create_app(); routes = [str(r) for r in app.url_map.iter_rules() if 'ai-coach' in str(r)]; print(len(routes))" 2>/dev/null | tr -d '\r')

if [ "$ROUTE_COUNT" -ge 5 ]; then
    echo "✓ All AI Coach routes registered ($ROUTE_COUNT routes)"
    docker-compose exec web python -c "from website import create_app; app = create_app(); routes = [str(r) for r in app.url_map.iter_rules() if 'ai-coach' in str(r)]; [print(f'  - {r}') for r in routes]" 2>/dev/null
else
    echo "✗ AI Coach routes not properly registered (found $ROUTE_COUNT, expected 5)"
    exit 1
fi
echo ""

# Test API endpoint
echo "Testing API endpoint..."
API_RESPONSE=$(docker-compose exec web curl -s http://localhost:8000/api/ai-coach/conversations)
if echo "$API_RESPONSE" | grep -q "Authentication required"; then
    echo "✓ API endpoint responding correctly"
else
    echo "✗ API endpoint not responding as expected"
    echo "Response: $API_RESPONSE"
    exit 1
fi
echo ""

echo "========================================="
echo "✓ AI Coach Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Purge Cloudflare cache:"
echo "   - Go to Cloudflare dashboard"
echo "   - Navigate to Caching > Configuration"
echo "   - Click 'Purge Everything'"
echo "   - Wait 2-3 minutes for propagation"
echo ""
echo "2. Access the AI Coach:"
echo "   - URL: https://vitruvian.bowmanhomelabtech.net/health-and-fitness/ai-coach"
echo "   - Login with your credentials"
echo "   - The AI Coach link should appear in Health & Fitness navigation"
echo ""
echo "3. Test the functionality:"
echo "   - Send a test message like: 'I weighed myself today at 175 lbs'"
echo "   - AI should respond and suggest creating a health metric record"
echo "   - Review and save the record to database"
echo ""
echo "If you still don't see the AI Coach link after purging cache:"
echo "- Try accessing with cache-busting: ?v=$(date +%s)"
echo "- Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)"
echo "- Enable Cloudflare Development Mode for 3 hours to bypass cache"
echo ""
