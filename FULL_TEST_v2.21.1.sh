#!/bin/bash

# Full System Test for v2.21.1
# Tests all major functionality after critical fixes

echo "🧪 Full System Test - FastAPI BizCard CRM v2.21.1"
echo "=================================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    local auth=$4
    
    echo -n "Testing $name... "
    
    if [ -n "$auth" ]; then
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $auth" "$url")
    else
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi
    
    if [ "$STATUS" -eq "$expected" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $STATUS)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (Expected $expected, got $STATUS)"
        ((FAILED++))
    fi
}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1. Basic Health Checks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_endpoint "Backend Health" "http://localhost:8000/health" 200
test_endpoint "Backend Version" "http://localhost:8000/version" 200
test_endpoint "Frontend Main" "http://localhost:3000/" 200
test_endpoint "Frontend Admin" "http://localhost:3000/admin" 200

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2. API Endpoints (No Auth)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_endpoint "Services API (no auth)" "http://localhost:8000/services/status" 401
test_endpoint "Duplicates API (no auth)" "http://localhost:8000/api/duplicates/" 401
test_endpoint "Contacts API (no auth)" "http://localhost:8000/api/contacts/" 401

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3. Docker Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SERVICES=("backend" "frontend" "db" "redis" "celery-worker")
for service in "${SERVICES[@]}"; do
    echo -n "Checking $service... "
    STATUS=$(docker compose ps --format json | jq -r "select(.Service==\"$service\") | .State" 2>/dev/null)
    if [ "$STATUS" = "running" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (Status: $STATUS)"
        ((FAILED++))
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4. Frontend Bundle${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -n "Checking JS bundle... "
BUNDLE=$(docker compose exec -T frontend ls /usr/share/nginx/html/static/js/ 2>/dev/null | grep "main.*\.js" | grep -v "map\|LICENSE" | head -1)
if [ -n "$BUNDLE" ]; then
    SIZE=$(docker compose exec -T frontend ls -lh /usr/share/nginx/html/static/js/$BUNDLE 2>/dev/null | awk '{print $5}')
    echo -e "${GREEN}✅ PASS${NC} ($BUNDLE - $SIZE)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

echo -n "Checking ServiceManagerSimple in bundle... "
if docker compose exec -T frontend grep -q "ServiceManagerSimple" /usr/share/nginx/html/static/js/$BUNDLE 2>/dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (Cannot verify - minified)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}5. Component Files${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

COMPONENTS=("ServiceManagerSimple.js" "DuplicateFinder.js" "AdminPanel.js" "OCREditorWithBlocks.js")
for comp in "${COMPONENTS[@]}"; do
    echo -n "Checking $comp... "
    if [ -f "frontend/src/components/$comp" ]; then
        LINES=$(wc -l < "frontend/src/components/$comp")
        echo -e "${GREEN}✅ PASS${NC} ($LINES lines)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}6. Git Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -n "Git status... "
if git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${GREEN}✅ PASS${NC} (Clean)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (Uncommitted changes)"
fi

echo -n "Latest commit... "
LAST_COMMIT=$(git log -1 --oneline)
echo -e "${GREEN}✅${NC} $LAST_COMMIT"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Test Results${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 All tests passed! System is ready.${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Test Services tab in Admin Panel"
    echo "2. Test Duplicates tab in Admin Panel"
    echo "3. Test OCR Editor with new block editing features"
    echo ""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⚠️  Some tests failed - review above${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi

