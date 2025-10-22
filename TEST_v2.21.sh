#!/bin/bash

# Test Script for v2.21.0
# Tests OCR Editor and Services functionality

echo "🧪 Testing FastAPI BizCard CRM v2.21.0"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3
    local auth=$4
    
    echo -n "Testing $name... "
    
    if [ -n "$auth" ]; then
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $auth" "$url")
    else
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi
    
    if [ "$STATUS" -eq "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $STATUS)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (Expected $expected_code, got $STATUS)"
        ((FAILED++))
    fi
}

echo "🔍 Testing Backend API Endpoints"
echo "--------------------------------"

# Test health endpoint
test_endpoint "Health Check" "http://localhost:8000/health" 200

# Test version endpoint
test_endpoint "Version Check" "http://localhost:8000/version" 200

# Test duplicates endpoint (should return 401 without auth)
test_endpoint "Duplicates (no auth)" "http://localhost:8000/api/duplicates/?threshold=0.6" 401

# Test system resources
test_endpoint "System Resources" "http://localhost:8000/system/resources" 200

echo ""
echo "🌐 Testing Frontend"
echo "-------------------"

# Test frontend main page
test_endpoint "Frontend Main Page" "http://localhost:3000/" 200

# Check if main.js bundle exists
echo -n "Checking JS bundle... "
BUNDLE=$(docker compose exec -T frontend ls /usr/share/nginx/html/static/js/ 2>/dev/null | grep "main.*\.js" | head -1)
if [ -n "$BUNDLE" ]; then
    echo -e "${GREEN}✅ PASS${NC} (Found: $BUNDLE)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} (Bundle not found)"
    ((FAILED++))
fi

echo ""
echo "🐳 Testing Docker Services"
echo "--------------------------"

# Check if containers are running
SERVICES=("backend" "frontend" "db" "redis")
for service in "${SERVICES[@]}"; do
    echo -n "Checking $service... "
    STATUS=$(docker compose ps --format json | jq -r "select(.Service==\"$service\") | .State" 2>/dev/null)
    if [ "$STATUS" = "running" ]; then
        echo -e "${GREEN}✅ PASS${NC} (Running)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (Not running)"
        ((FAILED++))
    fi
done

echo ""
echo "📊 Testing Service Management"
echo "------------------------------"

# Test services endpoint (requires admin auth - will fail with 401/403)
echo -n "Testing Services API... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/services/status")
if [ "$STATUS" -eq 401 ] || [ "$STATUS" -eq 403 ]; then
    echo -e "${GREEN}✅ PASS${NC} (Endpoint exists, requires auth)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (Unexpected status: $STATUS)"
fi

echo ""
echo "🎨 Testing OCR Editor Components"
echo "---------------------------------"

# Check if OCREditorWithBlocks.js exists
echo -n "Checking OCR Editor file... "
if [ -f "frontend/src/components/OCREditorWithBlocks.js" ]; then
    LINES=$(wc -l < frontend/src/components/OCREditorWithBlocks.js)
    echo -e "${GREEN}✅ PASS${NC} ($LINES lines)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} (File not found)"
    ((FAILED++))
fi

# Check if new OCR functions exist in the file
echo -n "Checking OCR editing functions... "
if grep -q "handleDeleteBlock\|handleAddBlock\|handleEditBlockText\|handleSplitBlock" frontend/src/components/OCREditorWithBlocks.js; then
    echo -e "${GREEN}✅ PASS${NC} (Functions found)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} (Functions not found)"
    ((FAILED++))
fi

echo ""
echo "📊 Test Results"
echo "==============="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed${NC}"
    exit 1
fi

