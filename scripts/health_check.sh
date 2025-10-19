#!/bin/bash

# BizCard CRM - Health Check Script
# Checks the health of all services and sends alerts if needed

set -e

# Configuration
SERVICES=("bizcard-frontend" "bizcard-backend" "bizcard-db" "bizcard-grafana" "bizcard-prometheus")
ALERT_FILE="/tmp/bizcard_health_alerts.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Initialize alert flag
ALERT=0

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                 BizCard CRM - Health Check Report                        ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Timestamp: $(date +'%Y-%m-%d %H:%M:%S')"
echo ""

# Check Docker containers
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐳 Docker Containers Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for service in "${SERVICES[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null || echo "unknown")
        health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "none")
        
        if [ "$status" == "running" ]; then
            if [ "$health" == "healthy" ] || [ "$health" == "none" ]; then
                echo -e "  ✅ ${service}: ${GREEN}Running${NC} $([ "$health" != "none" ] && echo "(Health: $health)")"
            else
                echo -e "  ⚠️  ${service}: ${YELLOW}Running${NC} (Health: ${YELLOW}${health}${NC})"
                ALERT=1
            fi
        else
            echo -e "  ❌ ${service}: ${RED}${status}${NC}"
            ALERT=1
        fi
    else
        echo -e "  ❌ ${service}: ${RED}Not Found${NC}"
        ALERT=1
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Service Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Frontend
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "  ✅ Frontend (Port 3000): ${GREEN}Accessible${NC}"
else
    echo -e "  ❌ Frontend (Port 3000): ${RED}Not Accessible${NC}"
    ALERT=1
fi

# Check Backend API
if curl -sf http://localhost:8000/version > /dev/null 2>&1; then
    version=$(curl -s http://localhost:8000/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo -e "  ✅ Backend API (Port 8000): ${GREEN}Accessible${NC} (Version: $version)"
else
    echo -e "  ❌ Backend API (Port 8000): ${RED}Not Accessible${NC}"
    ALERT=1
fi

# Check Grafana
if curl -sf http://localhost:3001/api/health > /dev/null 2>&1; then
    echo -e "  ✅ Grafana (Port 3001): ${GREEN}Accessible${NC}"
else
    echo -e "  ❌ Grafana (Port 3001): ${RED}Not Accessible${NC}"
    ALERT=1
fi

# Check Prometheus
if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "  ✅ Prometheus (Port 9090): ${GREEN}Accessible${NC}"
else
    echo -e "  ❌ Prometheus (Port 9090): ${RED}Not Accessible${NC}"
    ALERT=1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 Database Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker exec bizcard-db pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "  ✅ PostgreSQL: ${GREEN}Ready${NC}"
    
    # Get database size
    db_size=$(docker exec bizcard-db psql -U postgres -d bizcard_crm -t -c "SELECT pg_size_pretty(pg_database_size('bizcard_crm'));" 2>/dev/null | xargs || echo "unknown")
    echo "     Database size: $db_size"
    
    # Get table counts
    contacts_count=$(docker exec bizcard-db psql -U postgres -d bizcard_crm -t -c "SELECT COUNT(*) FROM contacts;" 2>/dev/null | xargs || echo "0")
    users_count=$(docker exec bizcard-db psql -U postgres -d bizcard_crm -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs || echo "0")
    tags_count=$(docker exec bizcard-db psql -U postgres -d bizcard_crm -t -c "SELECT COUNT(*) FROM tags;" 2>/dev/null | xargs || echo "0")
    groups_count=$(docker exec bizcard-db psql -U postgres -d bizcard_crm -t -c "SELECT COUNT(*) FROM groups;" 2>/dev/null | xargs || echo "0")
    
    echo "     Contacts: $contacts_count | Users: $users_count | Tags: $tags_count | Groups: $groups_count"
else
    echo -e "  ❌ PostgreSQL: ${RED}Not Ready${NC}"
    ALERT=1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 System Resources"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# CPU Load
load_avg=$(uptime | awk -F'load average:' '{print $2}' | xargs)
echo "  CPU Load Average: $load_avg"

# Memory
memory_info=$(free -h | awk '/^Mem:/ {print "Total: "$2", Used: "$3", Free: "$4}')
echo "  Memory: $memory_info"

# Disk Space
disk_info=$(df -h / | awk 'NR==2 {print "Total: "$2", Used: "$3" ("$5"), Available: "$4}')
echo "  Disk: $disk_info"

# Check if disk usage is over 90%
disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 90 ]; then
    echo -e "  ⚠️  ${YELLOW}WARNING: Disk usage is above 90%!${NC}"
    ALERT=1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔥 Recent Errors (last 24 hours)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for errors in backend logs
backend_errors=$(docker logs bizcard-backend --since 24h 2>&1 | grep -i "error\|exception\|fatal" | wc -l)
if [ "$backend_errors" -gt 0 ]; then
    echo -e "  ⚠️  Backend: ${YELLOW}${backend_errors} errors found${NC}"
    ALERT=1
else
    echo -e "  ✅ Backend: ${GREEN}No errors${NC}"
fi

# Check for errors in Nginx logs
if [ -f "/var/log/nginx/error.log" ]; then
    nginx_errors=$(sudo grep -i "error" /var/log/nginx/error.log 2>/dev/null | wc -l)
    if [ "$nginx_errors" -gt 10 ]; then
        echo -e "  ⚠️  Nginx: ${YELLOW}${nginx_errors} errors in log${NC}"
    else
        echo -e "  ✅ Nginx: ${GREEN}No critical errors${NC}"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Summary
if [ $ALERT -eq 0 ]; then
    echo -e "✅ ${GREEN}All systems operational!${NC}"
else
    echo -e "⚠️  ${YELLOW}Some issues detected! Please review the report above.${NC}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit $ALERT

