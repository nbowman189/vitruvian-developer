#!/bin/bash
# Database Rebuild Script
# Completely rebuilds the database container and runs migrations

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Determine which docker-compose files to use
COMPOSE_FILES="-f docker-compose.yml"
ENVIRONMENT="local"

# Check for remote flag
if [ "$1" == "--remote" ] || [ "$1" == "-r" ]; then
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.remote.yml"
    ENVIRONMENT="remote"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔄 Database Rebuild Script (${ENVIRONMENT})${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Step 1: Stop all containers
echo -e "\n${YELLOW}1️⃣  Stopping containers...${NC}"
docker-compose $COMPOSE_FILES down
echo -e "${GREEN}✓ Containers stopped${NC}"

# Step 2: Remove database volume
echo -e "\n${YELLOW}2️⃣  Removing database volume...${NC}"
docker volume rm primary-assistant_postgres_data 2>/dev/null || echo -e "${YELLOW}⚠ Volume may not exist${NC}"
echo -e "${GREEN}✓ Database volume removed${NC}"

# Step 3: Rebuild and start containers
echo -e "\n${YELLOW}3️⃣  Rebuilding containers (this may take 1-2 minutes)...${NC}"
docker-compose $COMPOSE_FILES up -d --build
echo -e "${GREEN}✓ Containers started${NC}"

# Step 4: Wait for database to be healthy
echo -e "\n${YELLOW}4️⃣  Waiting for database to be healthy...${NC}"
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker-compose $COMPOSE_FILES exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "\n${RED}✗ Database failed to become healthy${NC}"
    echo -e "${YELLOW}Check logs: docker-compose $COMPOSE_FILES logs db${NC}"
    exit 1
fi

# Step 5: Wait a bit more for database to fully initialize
echo -e "\n${YELLOW}5️⃣  Waiting for database to fully initialize...${NC}"
sleep 5
echo -e "${GREEN}✓ Database initialized${NC}"

# Step 6: Run database migrations
echo -e "\n${YELLOW}6️⃣  Running database migrations...${NC}"
docker-compose $COMPOSE_FILES exec -T web sh -c "cd /app/website && flask db upgrade"
echo -e "${GREEN}✓ Migrations complete${NC}"

# Step 7: Wait for web container to be healthy
echo -e "\n${YELLOW}7️⃣  Waiting for web container to be healthy...${NC}"
MAX_WAIT=60
WAITED=0

if [ "$ENVIRONMENT" == "remote" ]; then
    HEALTH_URL="http://localhost/api/health"
else
    HEALTH_URL="http://localhost:8001/api/health"
fi

while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -sf $HEALTH_URL > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Web container is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "\n${RED}✗ Web container failed to become healthy${NC}"
    echo -e "${YELLOW}Check logs: docker-compose $COMPOSE_FILES logs web${NC}"
    exit 1
fi

# Step 8: Ask about admin user creation
echo -e "\n${YELLOW}8️⃣  Create admin user?${NC}"
read -p "Create admin user (username: admin, password: admin123)? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    docker-compose $COMPOSE_FILES exec -T web python /app/website/scripts/create_admin_user.py
    echo -e "${GREEN}✓ Admin user created${NC}"
else
    echo -e "${YELLOW}⊘ Skipped admin user creation${NC}"
fi

# Step 9: Ask about sample data
echo -e "\n${YELLOW}9️⃣  Populate sample data?${NC}"
read -p "Populate sample health/fitness data? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "/Users/nathanbowman/primary-assistant/scripts/populate_sample_data.sh" ]; then
        /Users/nathanbowman/primary-assistant/scripts/populate_sample_data.sh
        echo -e "${GREEN}✓ Sample data populated${NC}"
    else
        echo -e "${RED}✗ Sample data script not found${NC}"
    fi
else
    echo -e "${YELLOW}⊘ Skipped sample data${NC}"
fi

# Step 10: Show final status
echo -e "\n${YELLOW}🔟 Final container status:${NC}"
docker-compose $COMPOSE_FILES ps

# Success message
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Database Rebuild Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ "$ENVIRONMENT" == "remote" ]; then
    echo -e "\n${BLUE}📊 Application Access:${NC}"
    echo -e "   • Dashboard: https://vitruvian.bowmanhomelabtech.net/dashboard"
    echo -e "   • Login: https://vitruvian.bowmanhomelabtech.net/auth/login"
else
    echo -e "\n${BLUE}📊 Application Access:${NC}"
    echo -e "   • Dashboard: http://localhost:8001/dashboard"
    echo -e "   • Login: http://localhost:8001/auth/login"
fi

echo -e "\n${BLUE}🔍 Useful commands:${NC}"
echo -e "   • View logs: docker-compose $COMPOSE_FILES logs -f web"
echo -e "   • Check status: docker-compose $COMPOSE_FILES ps"
echo -e "   • Stop containers: docker-compose $COMPOSE_FILES down"
echo ""
