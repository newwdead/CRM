#!/bin/bash

GRAFANA_URL="http://localhost:3001"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

echo "🔧 Исправление импорта Grafana Dashboards"
echo "=========================================="
echo ""

# Function to import dashboard
import_dashboard() {
    local file=$1
    local title=$(basename "$file" .json)
    
    echo "📊 Импорт: $title"
    
    # Read dashboard JSON and wrap it properly
    dashboard_content=$(cat "$file")
    
    # Create proper import payload
    payload=$(jq -n \
        --argjson dashboard "$dashboard_content" \
        '{
            dashboard: $dashboard.dashboard,
            overwrite: true,
            message: "Auto-imported dashboard"
        }')
    
    # Import dashboard
    result=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        -d "$payload" \
        "$GRAFANA_URL/api/dashboards/db")
    
    # Check result
    if echo "$result" | jq -e '.status == "success"' > /dev/null 2>&1; then
        uid=$(echo "$result" | jq -r '.uid')
        echo "   ✅ Успешно! UID: $uid"
        return 0
    else
        error=$(echo "$result" | jq -r '.message // .error // "Unknown error"')
        echo "   ❌ Ошибка: $error"
        return 1
    fi
}

# Import all dashboards
success_count=0
fail_count=0

for dashboard in monitoring/grafana/dashboards/*.json; do
    if [ -f "$dashboard" ]; then
        if import_dashboard "$dashboard"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
        echo ""
    fi
done

echo "=========================================="
echo "✅ Успешно: $success_count"
echo "❌ Ошибок: $fail_count"
echo ""

# List imported dashboards
echo "📋 Список dashboards в Grafana:"
curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" \
    "$GRAFANA_URL/api/search?type=dash-db" | \
    jq -r '.[] | "  ✅ \(.title)"'

echo ""
echo "Откройте: https://monitoring.ibbase.ru/dashboards"
