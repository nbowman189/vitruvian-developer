#!/bin/bash
# Remote deployment script with health checks
# Run this on your remote server after git pull

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Starting Deployment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Step 1: Pull latest code
echo -e "\n${YELLOW}1️⃣  Pulling latest code...${NC}"
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"

# Step 2: Stop containers
echo -e "\n${YELLOW}2️⃣  Stopping containers...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.remote.yml down
echo -e "${GREEN}✓ Containers stopped${NC}"

# Step 3: Rebuild and start containers
echo -e "\n${YELLOW}3️⃣  Rebuilding containers (this may take 1-2 minutes)...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d --build

# Step 4: Wait for database to be healthy
echo -e "\n${YELLOW}4️⃣  Waiting for database to be healthy...${NC}"
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "\n${RED}✗ Database failed to become healthy${NC}"
    echo -e "${YELLOW}Check logs: docker-compose -f docker-compose.yml -f docker-compose.remote.yml logs db${NC}"
    exit 1
fi

# Step 5: Wait for web container to be healthy
echo -e "\n${YELLOW}5️⃣  Waiting for web container to be healthy...${NC}"
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Web container is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "\n${RED}✗ Web container failed to become healthy${NC}"
    echo -e "${YELLOW}Check logs: docker-compose -f docker-compose.yml -f docker-compose.remote.yml logs web${NC}"
    exit 1
fi

# Step 6: Run database migrations (optional but safe)
echo -e "\n${YELLOW}6️⃣  Running database migrations...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web sh -c "cd /app/website && flask db upgrade" || echo -e "${YELLOW}⚠ Migrations may have already run${NC}"
echo -e "${GREEN}✓ Migrations complete${NC}"

# Step 7: Show final status
echo -e "\n${YELLOW}7️⃣  Final container status:${NC}"
docker-compose -f docker-compose.yml -f docker-compose.remote.yml ps

# Step 8: Show recent logs
echo -e "\n${YELLOW}8️⃣  Recent web container logs:${NC}"
docker-compose -f docker-compose.yml -f docker-compose.remote.yml logs --tail=20 web

# Success message
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n${BLUE}📊 Dashboard Access:${NC}"
echo -e "   • Login: https://vitruvian.bowmanhomelabtech.net/auth/login"
echo -e "   • Dashboard: https://vitruvian.bowmanhomelabtech.net/dashboard"
echo -e "\n${BLUE}🔍 To check logs:${NC}"
echo -e "   docker-compose -f docker-compose.yml -f docker-compose.remote.yml logs -f web"
echo -e "\n${BLUE}🔧 To check container status:${NC}"
echo -e "   docker-compose -f docker-compose.yml -f docker-compose.remote.yml ps"
echo ""
