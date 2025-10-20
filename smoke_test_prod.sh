#!/bin/bash
# Production Smoke Tests for ibbase v2.4

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║           🔥 PRODUCTION SMOKE TESTS - ibbase.ru                         ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"
    
    echo -n "Testing: $name ... "
    response=$(curl -s -o /dev/null -w "%{http_code}" -k "$url" 2>&1)
    
    if [ "$response" == "$expected_code" ]; then
        echo "✅ PASS (HTTP $response)"
        ((PASSED++))
    else
        echo "❌ FAIL (Expected $expected_code, got $response)"
        ((FAILED++))
    fi
}

test_json_endpoint() {
    local name="$1"
    local url="$2"
    local search_string="$3"
    
    echo -n "Testing: $name ... "
    response=$(curl -s -k "$url" 2>&1)
    
    if echo "$response" | grep -q "$search_string"; then
        echo "✅ PASS (Found: $search_string)"
        ((PASSED++))
    else
        echo "❌ FAIL (Not found: $search_string)"
        echo "   Response: ${response:0:100}..."
        ((FAILED++))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. FRONTEND TESTS (ibbase.ru)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "Frontend HTTPS" "https://ibbase.ru" "200"
test_endpoint "Frontend HTTP redirect" "http://ibbase.ru" "301"
test_endpoint "WWW redirect" "https://www.ibbase.ru" "200"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. API TESTS (api.ibbase.ru)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_json_endpoint "API Health" "https://api.ibbase.ru/health" '"status":"ok"'
test_json_endpoint "API Version" "https://api.ibbase.ru/version" '"version"'
test_endpoint "API Docs" "https://api.ibbase.ru/docs" "200"
test_endpoint "API Metrics" "https://api.ibbase.ru/metrics" "200"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. MONITORING TESTS (monitoring.ibbase.ru)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "Grafana" "https://monitoring.ibbase.ru" "200"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. SSL CERTIFICATE TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -n "Testing: SSL Certificate validity ... "
cert_info=$(echo | openssl s_client -servername ibbase.ru -connect ibbase.ru:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ PASS"
    echo "$cert_info" | grep "notAfter" | sed 's/^/   /'
    ((PASSED++))
else
    echo "❌ FAIL"
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. DOCKER SERVICES STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
services=("bizcard-frontend" "bizcard-backend" "bizcard-db" "bizcard-redis" "bizcard-celery-worker")
for service in "${services[@]}"; do
    echo -n "Testing: $service ... "
    if docker ps | grep -q "$service"; then
        status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null)
        if [ "$status" == "running" ]; then
            echo "✅ PASS (running)"
            ((PASSED++))
        else
            echo "❌ FAIL (status: $status)"
            ((FAILED++))
        fi
    else
        echo "❌ FAIL (not found)"
        ((FAILED++))
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. DATABASE CONNECTION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -n "Testing: PostgreSQL connection ... "
if docker exec bizcard-db psql -U postgres -d bizcard_crm -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL"
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. REDIS CONNECTION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -n "Testing: Redis connection ... "
if docker exec bizcard-redis redis-cli ping | grep -q "PONG"; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL"
    ((FAILED++))
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                        TEST RESULTS SUMMARY                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
TOTAL=$((PASSED + FAILED))
SUCCESS_RATE=$((PASSED * 100 / TOTAL))
echo "  Total Tests:    $TOTAL"
echo "  ✅ Passed:      $PASSED"
echo "  ❌ Failed:      $FAILED"
echo "  Success Rate:   $SUCCESS_RATE%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! Production is HEALTHY! 🎉"
    echo ""
    exit 0
else
    echo "⚠️  Some tests failed. Please review the output above."
    echo ""
    exit 1
fi

