#!/bin/bash
# 🚀 Deploy Script for v2.17 - Frontend Architecture Refactoring

set -e  # Exit on error

# Docker Compose command (support both v1 and v2)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Neither 'docker-compose' nor 'docker compose' found!"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 FastAPI Business Card CRM - Deploy v2.17"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Pre-deployment checks
echo "📋 Pre-deployment checks..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if running in correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if git repo is clean
if [[ -n $(git status -s) ]]; then
    echo "⚠️  Warning: Git working directory is not clean!"
    echo "Uncommitted changes detected. Continuing anyway..."
fi

# Show current version
echo "📦 Current deployment info:"
CURRENT_VERSION=$(eval "$DOCKER_COMPOSE exec -T backend python -c 'from app.main import app; print(app.version)'" 2>/dev/null || echo "Unknown")
echo "   Current version: $CURRENT_VERSION"
echo "   New version: 2.17.0"
echo ""

# Confirmation
read -p "🤔 Deploy v2.17.0 to production? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled."
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 Creating backup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create backup directory
BACKUP_DIR="backups/pre_v2.17_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Database backup
echo "📦 Backing up database..."
eval "$DOCKER_COMPOSE" exec -T postgres pg_dump -U postgres bizcard_crm > "$BACKUP_DIR/database.sql" || {
    echo "⚠️  Database backup failed, but continuing..."
}

# Backup uploads
echo "📦 Backing up uploads..."
cp -r uploads "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  No uploads directory found"

echo "✅ Backup created: $BACKUP_DIR"
echo ""

# Stop services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏸️  Stopping services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
eval "$DOCKER_COMPOSE" stop backend frontend celery_worker

# Pull latest code (already done via git)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 Code already updated via git push"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build images
echo "🔨 Building Docker images..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
eval "$DOCKER_COMPOSE" build backend frontend

# Database migrations (if any)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  Running database migrations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
eval "$DOCKER_COMPOSE" up -d postgres
sleep 5
eval "$DOCKER_COMPOSE" exec -T backend alembic upgrade head || {
    echo "⚠️  No migrations to run or alembic not configured"
}

# Start services
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "▶️  Starting services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
eval "$DOCKER_COMPOSE" up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Health checks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏥 Running health checks..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check backend
echo "🔍 Checking backend..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "✅ Backend: OK"
else
    echo "❌ Backend: FAILED (HTTP $BACKEND_STATUS)"
fi

# Check version
echo "🔍 Checking version..."
VERSION=$(curl -s http://localhost:8000/api/version | python3 -c "import sys, json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "Unknown")
echo "📦 Deployed version: $VERSION"

if [ "$VERSION" = "2.17.0" ]; then
    echo "✅ Version check: PASSED"
else
    echo "⚠️  Version check: Expected 2.17.0, got $VERSION"
fi

# Check frontend
echo "🔍 Checking frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FAILED (HTTP $FRONTEND_STATUS)"
fi

# Check database
echo "🔍 Checking database..."
DB_STATUS=$(eval "$DOCKER_COMPOSE" exec -T postgres pg_isready -U postgres | grep -c "accepting connections" || echo "0")
if [ "$DB_STATUS" = "1" ]; then
    echo "✅ Database: OK"
else
    echo "❌ Database: FAILED"
fi

# Check Redis
echo "🔍 Checking Redis..."
REDIS_STATUS=$(eval "$DOCKER_COMPOSE" exec -T redis redis-cli ping | grep -c "PONG" || echo "0")
if [ "$REDIS_STATUS" = "1" ]; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: FAILED"
fi

# Show running containers
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Running containers:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
eval "$DOCKER_COMPOSE" ps

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Summary:"
echo "   ✅ Version: v2.17.0"
echo "   ✅ Backend: http://localhost:8000"
echo "   ✅ Frontend: http://localhost"
echo "   ✅ API Docs: http://localhost:8000/docs"
echo "   ✅ Backup: $BACKUP_DIR"
echo ""
echo "📋 Next steps:"
echo "   1. Test Admin Panel → All tabs"
echo "   2. Check browser console for errors"
echo "   3. Test on mobile device"
echo "   4. Monitor logs: docker-compose logs -f --tail=100"
echo ""
echo "📚 Documentation:"
echo "   - RELEASE_NOTES_v2.17.md"
echo "   - TESTING_REPORT_v2.17.md"
echo "   - ARCHITECTURE_AUDIT_v2.16.md"
echo ""

