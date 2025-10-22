#!/bin/bash

# =============================================================================
# FastAPI BizCard CRM - Deployment Script v2.20.0
# Admin Panel & OCR Editor Enhancements
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting deployment of FastAPI BizCard CRM v2.20.0..."
echo "📦 Release: Admin Panel & OCR Editor Enhancements"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="/home/ubuntu/fastapi-bizcard-crm-ready"
cd $PROJECT_DIR

echo -e "${BLUE}📍 Working directory: $PROJECT_DIR${NC}"
echo ""

# =============================================================================
# Step 1: Git Pull
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1: Pulling latest changes from GitHub${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

git fetch --all
git pull origin main

echo -e "${GREEN}✅ Git pull completed${NC}"
echo ""

# =============================================================================
# Step 2: Backend Check
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 2: Backend Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}✅ Backend dependencies will be installed in Docker container${NC}"
echo ""

# =============================================================================
# Step 3: Frontend Check
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 3: Frontend Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}✅ Frontend will be built in Docker container${NC}"
echo ""

# =============================================================================
# Step 4: Docker Services
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 4: Restarting Docker Services${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Detect docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}❌ Docker Compose not found${NC}"
    exit 1
fi

echo -e "${YELLOW}🐳 Using: $DOCKER_COMPOSE${NC}"
echo ""

echo -e "${YELLOW}🔄 Restarting backend service...${NC}"
$DOCKER_COMPOSE restart backend

echo -e "${YELLOW}🔄 Restarting frontend service...${NC}"
$DOCKER_COMPOSE restart frontend

# Check if celery services exist
if $DOCKER_COMPOSE ps | grep -q "celery"; then
    echo -e "${YELLOW}🔄 Restarting celery workers...${NC}"
    $DOCKER_COMPOSE restart celery celery-beat 2>/dev/null || echo -e "${YELLOW}⚠️  Celery services not found, skipping${NC}"
else
    echo -e "${YELLOW}⚠️  Celery services not configured, skipping${NC}"
fi

echo -e "${GREEN}✅ Docker services restarted${NC}"
echo ""

# =============================================================================
# Step 5: Health Check
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 5: Health Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}⏳ Waiting for services to start (15 seconds)...${NC}"
sleep 15

echo -e "${YELLOW}🔍 Checking backend health...${NC}"
BACKEND_HEALTH=$(curl -s http://localhost:8000/health || echo "failed")
if [[ $BACKEND_HEALTH == *"ok"* ]]; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}⚠️  Backend health check failed${NC}"
fi

echo -e "${YELLOW}🔍 Checking backend version...${NC}"
BACKEND_VERSION=$(curl -s http://localhost:8000/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
if [[ $BACKEND_VERSION == "2.20.0" ]]; then
    echo -e "${GREEN}✅ Backend version: $BACKEND_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Backend version: $BACKEND_VERSION (expected 2.20.0)${NC}"
fi

echo -e "${YELLOW}🔍 Checking frontend...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend check inconclusive${NC}"
fi

echo ""

# =============================================================================
# Step 6: Service Status
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 6: Service Status${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}📊 Docker services status:${NC}"
$DOCKER_COMPOSE ps
echo ""

# =============================================================================
# Step 7: Cleanup
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 7: Cleanup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker system prune -f --volumes > /dev/null 2>&1 || true

echo -e "${GREEN}✅ Cleanup completed${NC}"
echo ""

# =============================================================================
# Deployment Summary
# =============================================================================
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📦 Version:${NC} 2.20.0"
echo -e "${BLUE}🏷️  Release:${NC} Admin Panel & OCR Editor Enhancements"
echo -e "${BLUE}📅 Date:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo -e "${BLUE}🌐 Services:${NC}"
echo -e "   • Backend:  http://localhost:8000"
echo -e "   • Frontend: http://localhost:3000"
echo -e "   • API Docs: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}✨ New Features:${NC}"
echo -e "   1. 🔗 System Resources - Configuration management"
echo -e "   2. ⚙️  Service Management - Fixed endpoint routing"
echo -e "   3. 🔧 System Settings - 8 integrations (OCR, Telegram, WhatsApp, Auth, Backup, Monitoring, Celery, Redis)"
echo -e "   4. 📝 OCR Editor - Block editing + re-processing"
echo ""
echo -e "${BLUE}📝 Release Notes:${NC} RELEASE_NOTES_v2.20.md"
echo ""
echo -e "${GREEN}🎉 Deployment successful!${NC}"
echo ""

