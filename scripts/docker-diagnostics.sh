#!/bin/bash
# Docker Health Diagnostics Script
# Run this on your server to diagnose deployment issues

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_pass() {
    echo -e "${GREEN}✅${NC} $1"
}

print_fail() {
    echo -e "${RED}❌${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "           DOCKER HEALTH DIAGNOSTICS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Detect Docker Compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    COMPOSE_VERSION="v2"
else
    DOCKER_COMPOSE="docker-compose"
    COMPOSE_VERSION="v1 ($($DOCKER_COMPOSE --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' || echo 'unknown'))"
fi

# Test 1: Docker Compose Version
echo "1. Docker Compose Version:"
echo "   $COMPOSE_VERSION"
if [ "$COMPOSE_VERSION" != "v2" ]; then
    print_warn "Using docker-compose v1 which has known caching bugs"
    print_info "Consider upgrading to Docker Compose V2"
    print_info "See: https://docs.docker.com/compose/install/"
else
    print_pass "Using Docker Compose V2"
fi
echo ""

# Test 2: Environment File
echo "2. Environment File:"
if [ -f .env ]; then
    print_pass ".env file exists"

    if grep -q 'SECRET_KEY=your-secret' .env 2>/dev/null; then
        print_fail "SECRET_KEY is using placeholder value"
    else
        print_pass "SECRET_KEY is set"
    fi

    if grep -q 'POSTGRES_PASSWORD=your-secure' .env 2>/dev/null; then
        print_fail "POSTGRES_PASSWORD is using placeholder value"
    else
        print_pass "POSTGRES_PASSWORD is set"
    fi
else
    print_fail ".env file missing"
    print_info "Run: cp .env.example .env && nano .env"
fi
echo ""

# Test 3: Container Status
echo "3. Container Status:"
CONTAINER_OUTPUT=$($DOCKER_COMPOSE ps 2>&1)
CONTAINER_COUNT=$(echo "$CONTAINER_OUTPUT" | grep -c "Up" || echo "0")

if [ "$CONTAINER_COUNT" = "0" ]; then
    print_fail "No containers are running"
    echo ""
    echo "   Container details:"
    $DOCKER_COMPOSE ps 2>/dev/null | tail -n +2 | while read line; do
        if [ -n "$line" ]; then
            echo "   $line"
        fi
    done

    # Check if containers exist but are stopped
    ALL_CONTAINERS=$(docker ps -a --filter "name=vitruvian-developer" --filter "name=primary-assistant" --format "{{.Names}}" 2>/dev/null)
    if [ -n "$ALL_CONTAINERS" ]; then
        echo ""
        print_warn "Found stopped containers - possible ContainerConfig bug"
        print_info "Run the fix script: ./scripts/docker-fix-and-start.sh"
    else
        echo ""
        print_info "No containers found. You need to start the application:"
        print_info "Run: docker-compose up -d"
        print_info "Or use the fix script: ./scripts/docker-fix-and-start.sh"
    fi

    CONTAINERS_RUNNING=false
else
    print_pass "$CONTAINER_COUNT containers running"
    echo ""
    $DOCKER_COMPOSE ps
    CONTAINERS_RUNNING=true
fi
echo ""

# Only run container-specific tests if containers are running
if [ "$CONTAINERS_RUNNING" = "true" ]; then
    # Test 4: Database Health
    echo "4. Database Container:"
    if $DOCKER_COMPOSE exec -T db pg_isready -U postgres -d primary_assistant > /dev/null 2>&1; then
        print_pass "Database is ready"
    else
        print_fail "Database is not ready"
        print_info "Check logs: $DOCKER_COMPOSE logs db"
    fi
    echo ""

    # Test 5: Web Container Health
    echo "5. Web Container Health:"
    if $DOCKER_COMPOSE exec -T web curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        print_pass "Web container health endpoint responding"
    else
        print_fail "Web container health endpoint not responding"
        print_info "Check logs: $DOCKER_COMPOSE logs web"
    fi
    echo ""

    # Test 6: Nginx → Web Connection
    echo "6. Nginx → Web Connection:"
    if $DOCKER_COMPOSE exec -T nginx curl -f http://web:8000/api/health > /dev/null 2>&1; then
        print_pass "Nginx can reach web container"
    else
        print_fail "Nginx cannot reach web container"
        print_info "Check network: docker network inspect vitruvian-developer_frontend"
    fi
    echo ""

    # Test 7: External Access
    echo "7. External Access:"
    if curl -f -s http://localhost/api/health > /dev/null 2>&1; then
        print_pass "Application accessible from outside"
        HEALTH_OUTPUT=$(curl -s http://localhost/api/health)
        echo "   Response: $HEALTH_OUTPUT"
    else
        print_fail "Cannot access application from outside"
        print_info "Check nginx logs: $DOCKER_COMPOSE logs nginx"
    fi
    echo ""

    # Test 8: Recent Errors
    echo "8. Recent Errors:"

    WEB_ERRORS=$($DOCKER_COMPOSE logs web 2>&1 | grep -i "error\|exception\|traceback" | tail -5)
    if [ -n "$WEB_ERRORS" ]; then
        print_warn "Found errors in web container logs:"
        echo "$WEB_ERRORS" | while read line; do
            echo "   $line"
        done
    else
        print_pass "No recent errors in web container"
    fi

    echo ""

    NGINX_ERRORS=$($DOCKER_COMPOSE logs nginx 2>&1 | grep -i "error" | grep -v "connect() failed" | tail -5)
    if [ -n "$NGINX_ERRORS" ]; then
        print_warn "Found errors in nginx container logs:"
        echo "$NGINX_ERRORS" | while read line; do
            echo "   $line"
        done
    else
        print_pass "No recent errors in nginx container"
    fi
    echo ""

else
    print_info "Skipping container health checks (containers not running)"
    echo ""

    # Check for recent build/startup errors
    echo "4. Recent Docker Logs:"
    RECENT_ERRORS=$($DOCKER_COMPOSE logs 2>&1 | grep -i "error\|failed\|exception" | tail -10)
    if [ -n "$RECENT_ERRORS" ]; then
        print_warn "Found recent errors in logs:"
        echo "$RECENT_ERRORS" | while read line; do
            echo "   $line"
        done
    else
        print_info "No recent error logs found"
    fi
    echo ""
fi

# Summary and Recommendations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "           SUMMARY & RECOMMENDATIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$CONTAINERS_RUNNING" = "false" ]; then
    echo "❌ ISSUE: Containers are not running"
    echo ""
    echo "Recommended actions:"
    echo "  1. Run the fix script (handles ContainerConfig bug):"
    echo "     ./scripts/docker-fix-and-start.sh"
    echo ""
    echo "  2. Or manually clean and restart:"
    echo "     $DOCKER_COMPOSE down -v --remove-orphans"
    echo "     docker rm -f \$(docker ps -aq --filter name=vitruvian-developer)"
    echo "     $DOCKER_COMPOSE build --no-cache"
    echo "     $DOCKER_COMPOSE up -d"
    echo ""
    echo "  3. View logs during startup:"
    echo "     $DOCKER_COMPOSE logs -f"
    echo ""
elif curl -f -s http://localhost/api/health > /dev/null 2>&1; then
    echo "✅ SUCCESS: All systems operational"
    echo ""
    echo "Application is running at: http://localhost"
    echo ""
else
    echo "⚠️  WARNING: Containers running but health checks failing"
    echo ""
    echo "Recommended actions:"
    echo "  1. Check web container logs:"
    echo "     $DOCKER_COMPOSE logs web | tail -50"
    echo ""
    echo "  2. Check nginx container logs:"
    echo "     $DOCKER_COMPOSE logs nginx | tail -50"
    echo ""
    echo "  3. Restart containers:"
    echo "     $DOCKER_COMPOSE restart"
    echo ""
    echo "  4. If issues persist, run fix script:"
    echo "     ./scripts/docker-fix-and-start.sh"
    echo ""
fi

echo "For more help, see: docs/docker/TROUBLESHOOTING.md"
echo ""
