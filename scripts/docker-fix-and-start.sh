#!/bin/bash
# Docker Fix and Start Script
# Handles ContainerConfig bug and starts containers cleanly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "           Docker Fix and Start Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Detect Docker Compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    print_status "Using Docker Compose V2"
else
    DOCKER_COMPOSE="docker-compose"
    print_warning "Using docker-compose V1 (version $(docker-compose --version | grep -oP '\d+\.\d+\.\d+'))"
    print_warning "This version has known caching bugs. Consider upgrading to Docker Compose V2."
fi
echo ""

# Step 1: Stop and remove existing containers
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Cleaning up existing containers..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

print_info "Stopping containers..."
$DOCKER_COMPOSE down -v --remove-orphans 2>/dev/null || true

print_info "Removing any leftover containers..."
docker rm -f vitruvian-developer-db vitruvian-developer-web vitruvian-developer-nginx 2>/dev/null || true
docker rm -f primary-assistant-db primary-assistant-web primary-assistant-nginx 2>/dev/null || true

print_info "Pruning stopped containers..."
docker container prune -f > /dev/null 2>&1 || true

print_status "Cleanup complete"
echo ""

# Step 2: Verify environment configuration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Verifying environment configuration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_info "Creating .env from .env.example..."
    cp .env.example .env

    # Generate SECRET_KEY
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    sed -i "s/SECRET_KEY=your-secret-key-here/SECRET_KEY=$SECRET_KEY/" .env

    print_warning "Please edit .env and set POSTGRES_PASSWORD before continuing!"
    print_info "Run: nano .env"
    exit 1
fi

# Check for placeholder values
if grep -q "SECRET_KEY=your-secret" .env; then
    print_error "SECRET_KEY is still set to placeholder value!"
    print_info "Generating new SECRET_KEY..."
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    sed -i "s/SECRET_KEY=your-secret-key-here/SECRET_KEY=$SECRET_KEY/" .env
    print_status "SECRET_KEY generated"
fi

if grep -q "POSTGRES_PASSWORD=your-secure" .env; then
    print_error "POSTGRES_PASSWORD is still set to placeholder value!"
    print_warning "Please set a secure password in .env before continuing!"
    exit 1
fi

print_status "Environment configuration valid"
echo ""

# Step 3: Build images (no cache to avoid ContainerConfig bug)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Building Docker images (this may take a few minutes)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

$DOCKER_COMPOSE build --no-cache

print_status "Images built successfully"
echo ""

# Step 4: Start containers
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Starting containers..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

$DOCKER_COMPOSE up -d

print_status "Containers started"
echo ""

# Step 5: Wait for containers to be healthy
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Waiting for containers to be healthy (up to 2 minutes)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TIMEOUT=120
ELAPSED=0
INTERVAL=5

while [ $ELAPSED -lt $TIMEOUT ]; do
    DB_HEALTH=$($DOCKER_COMPOSE ps db 2>/dev/null | grep -c "healthy" || echo "0")
    WEB_HEALTH=$($DOCKER_COMPOSE ps web 2>/dev/null | grep -c "healthy" || echo "0")
    NGINX_HEALTH=$($DOCKER_COMPOSE ps nginx 2>/dev/null | grep -c "healthy" || echo "0")

    if [ "$DB_HEALTH" = "1" ] && [ "$WEB_HEALTH" = "1" ] && [ "$NGINX_HEALTH" = "1" ]; then
        print_status "All containers are healthy!"
        break
    fi

    echo -n "."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""

if [ $ELAPSED -ge $TIMEOUT ]; then
    print_warning "Containers did not become healthy within 2 minutes"
    print_info "Checking container status..."
    $DOCKER_COMPOSE ps
    echo ""
    print_info "Recent logs:"
    $DOCKER_COMPOSE logs --tail=20
    exit 1
fi

echo ""

# Step 6: Verify deployment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Verifying deployment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test health endpoint
if curl -f -s http://localhost/api/health > /dev/null 2>&1; then
    print_status "Health endpoint responding"
else
    print_error "Health endpoint not responding"
    print_info "Run: curl http://localhost/api/health"
fi

# Show container status
echo ""
print_info "Container Status:"
$DOCKER_COMPOSE ps

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_status "Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Application URL: http://localhost"
echo "🏥 Health Check:    http://localhost/api/health"
echo ""
echo "Useful commands:"
echo "  View logs:        $DOCKER_COMPOSE logs -f"
echo "  Stop containers:  $DOCKER_COMPOSE down"
echo "  Restart:          $DOCKER_COMPOSE restart"
echo "  Run diagnostics:  ./scripts/docker-diagnostics.sh"
echo ""
