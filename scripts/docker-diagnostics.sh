#!/bin/bash
# Docker Health Diagnostics Script
# Run this on your server to diagnose deployment issues

echo "=== DOCKER HEALTH DIAGNOSTICS ==="
echo ""

echo "1. Container Status:"
docker-compose ps
echo ""

echo "2. Environment File:"
if [ -f .env ]; then
    echo "✅ .env exists"
    echo "SECRET_KEY set: $(grep -q 'SECRET_KEY=your-secret' .env && echo '❌ Using placeholder!' || echo '✅')"
    echo "POSTGRES_PASSWORD set: $(grep -q 'POSTGRES_PASSWORD=your-secure' .env && echo '❌ Using placeholder!' || echo '✅')"
else
    echo "❌ .env file missing!"
fi
echo ""

echo "3. Database Container:"
docker-compose exec db pg_isready -U postgres -d primary_assistant
echo ""

echo "4. Web Container Health:"
docker-compose exec web curl -f http://localhost:8000/api/health 2>/dev/null && echo "✅ Web healthy" || echo "❌ Web unhealthy"
echo ""

echo "5. Nginx → Web Connection:"
docker-compose exec nginx curl -f http://web:8000/api/health 2>/dev/null && echo "✅ Nginx can reach web" || echo "❌ Cannot reach web"
echo ""

echo "6. External Access:"
curl -f http://localhost/api/health 2>/dev/null && echo "✅ External access working" || echo "❌ External access failed"
echo ""

echo "7. Recent Errors (Web):"
docker-compose logs web | grep -i error | tail -10
echo ""

echo "8. Recent Errors (Nginx):"
docker-compose logs nginx | grep -i error | tail -10
echo ""

echo "9. Docker Compose Version:"
docker compose version || docker-compose --version
echo ""

echo "=== DIAGNOSTIC COMPLETE ==="
