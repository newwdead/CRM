#!/bin/bash

GRAFANA_URL="http://localhost:3001"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

echo "🚀 Импорт Grafana Dashboards"
echo "=============================="
echo ""

# Wait for Grafana to be ready
echo "⏳ Ожидание готовности Grafana..."
for i in {1..30}; do
  if curl -s -o /dev/null -w "%{http_code}" $GRAFANA_URL | grep -q "302\|200"; then
    echo "✅ Grafana готова!"
    break
  fi
  echo "   Попытка $i/30..."
  sleep 2
done

echo ""

# Create Prometheus datasource
echo "📊 Создание Prometheus datasource..."
curl -s -X POST -H "Content-Type: application/json" \
  -u $GRAFANA_USER:$GRAFANA_PASS \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://bizcard-prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }' \
  $GRAFANA_URL/api/datasources > /dev/null 2>&1

echo "✅ Datasource создан (или уже существует)"
echo ""

# Import dashboards
echo "📈 Импорт dashboards..."
echo ""

DASHBOARD_DIR="monitoring/grafana/dashboards"

for dashboard in $DASHBOARD_DIR/*.json; do
  filename=$(basename "$dashboard")
  echo "Импорт: $filename"
  
  # Wrap dashboard JSON in proper format
  cat > /tmp/dashboard_import.json << WRAPPER
{
  "dashboard": $(cat "$dashboard" | jq '.dashboard'),
  "overwrite": true,
  "inputs": [],
  "folderUid": ""
}
WRAPPER
  
  result=$(curl -s -X POST -H "Content-Type: application/json" \
    -u $GRAFANA_USER:$GRAFANA_PASS \
    -d @/tmp/dashboard_import.json \
    $GRAFANA_URL/api/dashboards/db)
  
  if echo "$result" | jq -e '.status == "success"' > /dev/null 2>&1; then
    echo "  ✅ Импортирован успешно"
  elif echo "$result" | jq -e '.message' > /dev/null 2>&1; then
    msg=$(echo "$result" | jq -r '.message')
    echo "  ⚠️  $msg"
  else
    echo "  ✅ OK"
  fi
  echo ""
done

rm -f /tmp/dashboard_import.json

echo "=============================="
echo "✅ Импорт завершен!"
echo ""
echo "Откройте Grafana: https://monitoring.ibbase.ru"
echo "Login: admin / admin"
