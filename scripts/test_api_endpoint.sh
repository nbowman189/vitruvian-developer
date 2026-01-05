#!/bin/bash
echo "=== Testing behavior logs endpoint ==="
echo ""
echo "1. Testing from inside web container (bypassing nginx):"
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web curl -s -w '\nHTTP Status: %{http_code}\n' 'http://localhost:8000/api/behavior/logs?start_date=2025-12-04&end_date=2026-01-03&per_page=1000' | head -20
echo ""
echo "2. Checking web container logs for the request:"
docker-compose -f docker-compose.yml -f docker-compose.remote.yml logs --tail=50 web | grep -i "behavior"
echo ""
echo "3. Checking nginx error log:"
docker exec primary-assistant-nginx tail -20 /var/log/nginx/error.log
