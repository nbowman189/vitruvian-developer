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
ROUTE_OUTPUT=$(docker-compose exec web python -c "from website import create_app; app = create_app(); routes = [str(r) for r in app.url_map.iter_rules() if 'ai-coach' in str(r)]; print(len(routes))" 2>&1)
ROUTE_COUNT=$(echo "$ROUTE_OUTPUT" | tail -1 | tr -d '\r')

if [ "$ROUTE_COUNT" = "5" ]; then
    echo "✓ All AI Coach routes registered ($ROUTE_COUNT routes)"
    docker-compose exec web python -c "from website import create_app; app = create_app(); routes = [str(r) for r in app.url_map.iter_rules() if 'ai-coach' in str(r)]; [print(f'  - {r}') for r in routes]" 2>&1 | grep -E "^\s+-\s+/"
else
    echo "✗ AI Coach routes not properly registered (found '$ROUTE_COUNT', expected 5)"
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
echo "=== CRITICAL: Purge Cloudflare Cache ==="
echo "The AI Coach link won't appear until you purge the cache!"
echo ""
echo "Steps to purge Cloudflare cache:"
echo "1. Go to Cloudflare dashboard"
echo "2. Navigate to Caching > Configuration"
echo "3. Click 'Purge Everything'"
echo "4. Wait 2-3 minutes for global propagation"
echo ""
echo "=== How to Access AI Coach ==="
echo ""
echo "Option 1: From Homepage (NEW!)"
echo "   - Go to: https://vitruvian.bowmanhomelabtech.net/"
echo "   - Scroll to 'The Synergy' section"
echo "   - Click 'Try AI Coach →' button in Fitness & Discipline card"
echo ""
echo "Option 2: Direct URL"
echo "   - https://vitruvian.bowmanhomelabtech.net/health-and-fitness/ai-coach"
echo "   - Login with your credentials if prompted"
echo ""
echo "Option 3: From Health & Fitness Navigation"
echo "   - Navigate to Health & Fitness project"
echo "   - Click 'AI Coach' link in navigation bar"
echo ""
echo "=== Testing the AI Coach ==="
echo ""
echo "1. Send a test message:"
echo "   'I weighed myself today at 175 lbs with 18% body fat'"
echo ""
echo "2. AI will respond conversationally AND suggest a health metric record"
echo ""
echo "3. Click 'Review & Save' to edit the suggested record"
echo ""
echo "4. Click 'Save to Database' to store it"
echo ""
echo "=== Troubleshooting ==="
echo ""
echo "If cache purge doesn't work immediately:"
echo "- Add ?v=$(date +%s) to URL to bypass cache"
echo "- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)"
echo "- Enable Cloudflare Development Mode (disables caching for 3 hours)"
echo ""
