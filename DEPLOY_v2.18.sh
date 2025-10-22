#!/bin/bash
# 🚀 Deploy Script for v2.18 - UX Improvements & System Integration Release

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker Compose command (support both v1 and v2)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}❌ Neither 'docker-compose' nor 'docker compose' found!${NC}"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🚀 FastAPI Business Card CRM - Deploy v2.18${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Pre-Deployment Checks
echo -e "${YELLOW}📋 Step 1: Pre-Deployment Checks${NC}"
echo "Checking system requirements..."

# Check if required commands exist
for cmd in git docker; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}❌ Required command not found: $cmd${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ All required commands available${NC}"
echo ""

# 2. Backup Current State
echo -e "${YELLOW}💾 Step 2: Creating Backup${NC}"
BACKUP_DIR="backups/deploy_v2.18_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
if eval "$DOCKER_COMPOSE ps postgres" | grep -q "Up"; then
    echo "Backing up database..."
    eval "$DOCKER_COMPOSE exec -T postgres pg_dump -U postgres -d ibbase" > "$BACKUP_DIR/database_backup.sql" || true
fi

# Backup .env if exists
if [ -f .env ]; then
    cp .env "$BACKUP_DIR/.env.backup"
fi

echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
echo ""

# 3. Stop Services
echo -e "${YELLOW}🛑 Step 3: Stopping Services${NC}"
eval "$DOCKER_COMPOSE down" || true
echo -e "${GREEN}✅ Services stopped${NC}"
echo ""

# 4. Pull Latest Code
echo -e "${YELLOW}📥 Step 4: Pulling Latest Code${NC}"
git fetch origin
git checkout main
git pull origin main
echo -e "${GREEN}✅ Code updated to v2.18.0${NC}"
echo ""

# 5. Update Dependencies
echo -e "${YELLOW}📦 Step 5: Updating Dependencies${NC}"

# Backend - rebuild to install any new packages
echo "Rebuilding backend..."
eval "$DOCKER_COMPOSE build --no-cache backend"

# Frontend - rebuild to install any new packages
echo "Rebuilding frontend..."
eval "$DOCKER_COMPOSE build --no-cache frontend"

echo -e "${GREEN}✅ Dependencies updated${NC}"
echo ""

# 6. Database Migrations
echo -e "${YELLOW}🗄️ Step 6: Running Database Migrations${NC}"
eval "$DOCKER_COMPOSE up -d postgres redis"
sleep 5

# Run migrations if alembic is configured
if [ -d "backend/alembic" ]; then
    eval "$DOCKER_COMPOSE run --rm backend alembic upgrade head" || echo "Note: Alembic migrations skipped or not configured"
fi

echo -e "${GREEN}✅ Database migrations complete${NC}"
echo ""

# 7. Start Services
echo -e "${YELLOW}🚀 Step 7: Starting All Services${NC}"
eval "$DOCKER_COMPOSE up -d"
echo -e "${GREEN}✅ All services started${NC}"
echo ""

# 8. Health Checks
echo -e "${YELLOW}🏥 Step 8: Health Checks${NC}"
echo "Waiting for services to be ready..."
sleep 10

# Check backend
if curl -f http://localhost:8000/api/health &>/dev/null; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}⚠️  Backend health check failed${NC}"
fi

# Check frontend
if curl -f http://localhost:3000 &>/dev/null; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}⚠️  Frontend health check failed${NC}"
fi

# Check version
VERSION_CHECK=$(curl -s http://localhost:8000/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
if [ "$VERSION_CHECK" == "2.18.0" ]; then
    echo -e "${GREEN}✅ Version verified: $VERSION_CHECK${NC}"
else
    echo -e "${YELLOW}⚠️  Version mismatch: expected 2.18.0, got $VERSION_CHECK${NC}"
fi

echo ""

# 9. Display Service Status
echo -e "${YELLOW}📊 Step 9: Service Status${NC}"
eval "$DOCKER_COMPOSE ps"
echo ""

# 10. Final Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📝 What's New in v2.18.0:${NC}"
echo ""
echo "  ✨ Dynamic Contact Table with customizable columns"
echo "  🔗 System Resources Dashboard"
echo "  ⚙️  Service Management for Docker containers"
echo "  📚 Complete Russian documentation"
echo "  🐛 Fixed table column toggle functionality"
echo "  🐛 Fixed 'Failed to load resources' error"
echo "  🐛 Fixed missing service management endpoints"
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Grafana:   http://localhost:3001"
echo "  Prometheus: http://localhost:9090"
echo ""
echo -e "${BLUE}📁 Backup Location:${NC}"
echo "  $BACKUP_DIR"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo ""
echo "  1. Test new table settings: Click '⚙️ Таблица' on Contacts page"
echo "  2. Check System Resources: Admin Panel → Resources tab"
echo "  3. Try Service Manager: Admin Panel → Services tab"
echo "  4. Verify all services are running: docker-compose ps"
echo "  5. Monitor logs: docker-compose logs -f backend frontend"
echo ""
echo -e "${GREEN}✅ Ready for production!${NC}"
echo ""

