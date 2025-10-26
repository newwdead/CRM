# 📊 Grafana Dashboards - Руководство

## ✅ ЧТО ИСПРАВЛЕНО

### Проблема:
После перезапуска контейнера Grafana **дашборды пропадали**, потому что не были настроены provisioning volumes.

### Решение:
```yaml
# docker-compose.monitoring-full.yml
volumes:
  - grafana_data:/var/lib/grafana                        # БД Grafana (сохраняется)
  - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro  # Provisioning config
  - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro  # Dashboards JSON files
```

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
monitoring/
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml        # Prometheus datasource config
│   │   └── dashboards/
│   │       └── dashboards.yml        # Dashboard provider config
│   └── dashboards/                   # ← JSON файлы дашбордов здесь!
│       ├── fastapi-crm-dashboard.json
│       ├── system-overview.json
│       └── application-metrics.json
└── grafana-data/                     # Volume с БД Grafana (создается Docker)
```

---

## 🔄 КАК РАБОТАЕТ AUTO-PROVISIONING

### 1. При запуске Grafana:

1. Монтирует `/etc/grafana/provisioning/` (read-only)
2. Читает конфигурацию из `provisioning/datasources/prometheus.yml`
3. Автоматически добавляет Prometheus datasource
4. Читает конфигурацию из `provisioning/dashboards/dashboards.yml`
5. Загружает все JSON файлы из `/var/lib/grafana/dashboards/`
6. Дашборды появляются в Grafana **автоматически!**

### 2. Периодически (каждые 10 секунд):

- Grafana проверяет изменения в JSON файлах
- Автоматически обновляет дашборды если файлы изменились

---

## 💾 КАК СОХРАНИТЬ НОВЫЙ ДАШБОРД

### Вариант 1: Через Web UI (рекомендуется)

1. **Создать/изменить дашборд в Grafana UI:**
   ```
   https://monitoring.ibbase.ru
   Login: admin / <your-password>
   ```

2. **Экспортировать JSON:**
   - Открыть дашборд
   - Dashboard Settings (⚙️) → JSON Model
   - Скопировать весь JSON
   
3. **Сохранить в файл на сервере:**
   ```bash
   cd /home/ubuntu/fastapi-bizcard-crm-ready
   
   # Создать файл дашборда
   cat > monitoring/grafana/dashboards/my-new-dashboard.json << 'EOF'
   {
     "title": "My Dashboard",
     "uid": "my-dashboard-uid",
     ...
   }
   EOF
   
   # Grafana автоматически подхватит через 10 секунд
   ```

### Вариант 2: Через API

```bash
# Получить JSON существующего дашборда
curl -s http://localhost:3001/api/dashboards/uid/fastapi-crm \
  -u admin:password | jq .dashboard > my-dashboard.json

# Сохранить в monitoring/grafana/dashboards/
mv my-dashboard.json monitoring/grafana/dashboards/
```

---

## 🔧 ВАЖНЫЕ МОМЕНТЫ

### ✅ Правильный формат JSON дашборда:

```json
{
  "title": "Dashboard Name",
  "uid": "unique-dashboard-id",
  "tags": ["tag1", "tag2"],
  "timezone": "browser",
  "schemaVersion": 38,
  "version": 1,
  "refresh": "30s",
  "panels": [...]
}
```

### ❌ НЕПРАВИЛЬНО (будет ошибка):

```json
{
  "dashboard": {
    "title": "...",
    ...
  }
}
```

**Причина:** Grafana provisioning ожидает JSON дашборда напрямую, без обертки `{"dashboard": {...}}`.

---

## 🚀 ТЕКУЩИЕ ДАШБОРДЫ

### 1. FastAPI CRM Dashboard (`fastapi-crm-dashboard.json`)
**UID:** `fastapi-crm`  
**Описание:** Основной дашборд приложения  
**Метрики:**
- HTTP Request Rate
- Request Duration
- Active Users
- Contact Operations
- OCR Processing
- Database Queries
- Cache Hit Rate
- Error Rate

### 2. System Overview (`system-overview.json`)
**UID:** `system-overview`  
**Описание:** Обзор системных метрик сервера  
**Метрики:**
- CPU Usage
- Memory Usage
- Disk I/O
- Network Traffic
- Load Average

### 3. Application Metrics (`application-metrics.json`)
**UID:** `application-metrics`  
**Описание:** Детальные метрики приложения  
**Метрики:**
- API Response Times
- Database Connection Pool
- Redis Operations
- Celery Tasks

---

## 🔍 ПРОВЕРКА ДАШБОРДОВ

### Проверить что дашборды загружены:

```bash
# Логи Grafana
docker logs bizcard-grafana --tail 50 | grep dashboard

# Должно быть:
# ✅ "starting to provision dashboards"
# ✅ "finished to provision dashboards"
# ❌ БЕЗ ошибок "Dashboard title cannot be empty"
```

### Проверить список дашбордов через API:

```bash
curl -s http://localhost:3001/api/search?type=dash-db \
  -u admin:password | jq '.[].title'
```

### Доступ к Grafana:

- **Локально:** `http://localhost:3001`
- **Публично:** `https://monitoring.ibbase.ru` (через Nginx + auth)

---

## 🛠️ ВОССТАНОВЛЕНИЕ ДАШБОРДОВ

### Если дашборды пропали:

```bash
# 1. Проверить volumes в docker-compose
grep -A 5 "grafana:" docker-compose.monitoring-full.yml

# 2. Проверить что файлы существуют
ls -la monitoring/grafana/dashboards/

# 3. Перезапустить Grafana
docker compose -f docker-compose.monitoring-full.yml restart grafana

# 4. Проверить логи
docker logs bizcard-grafana --tail 30 | grep dashboard
```

---

## 📋 BEST PRACTICES

### ✅ DO:

1. **Всегда сохраняйте дашборды в Git:**
   ```bash
   git add monitoring/grafana/dashboards/
   git commit -m "📊 Add new dashboard"
   ```

2. **Используйте уникальные UID для дашбордов:**
   ```json
   "uid": "my-unique-dashboard-2025"
   ```

3. **Добавляйте теги для группировки:**
   ```json
   "tags": ["application", "monitoring", "production"]
   ```

4. **Используйте version control для изменений:**
   ```json
   "version": 2  // Увеличивайте при изменении
   ```

### ❌ DON'T:

1. ❌ Не создавайте дашборды только через UI без сохранения в JSON
2. ❌ Не используйте абсолютные пути в queries
3. ❌ Не сохраняйте sensitive данные в дашбордах
4. ❌ Не удаляйте `grafana_data` volume (там БД Grafana)

---

## 🔒 БЕЗОПАСНОСТЬ

### Текущая конфигурация:

```yaml
ports:
  - "127.0.0.1:3001:3000"  # Только localhost!
```

- ✅ Grafana доступна **только локально** `:3001`
- ✅ Публичный доступ **только через Nginx** с аутентификацией
- ✅ `https://monitoring.ibbase.ru` - защищено SSL + Basic Auth

### Рекомендации:

1. Используйте сильный пароль для Grafana admin
2. Регулярно обновляйте Grafana: `docker pull grafana/grafana:latest`
3. Включите 2FA для admin аккаунта
4. Ограничьте права для viewer пользователей

---

## 📊 КАСТОМИЗАЦИЯ ДАШБОРДОВ

### Добавить новую панель:

```json
{
  "id": 10,
  "title": "My Custom Metric",
  "type": "timeseries",
  "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
  "targets": [{
    "expr": "my_custom_metric_total",
    "legendFormat": "{{instance}}"
  }],
  "fieldConfig": {
    "defaults": {
      "unit": "short",
      "color": {"mode": "palette-classic"}
    }
  }
}
```

### Доступные datasources:

- **Prometheus:** `http://bizcard-prometheus:9090`
- **URL в queries:** `prometheus` (Grafana автоматически использует настроенный datasource)

---

## 🔧 TROUBLESHOOTING

### Проблема: Дашборды не загружаются

**Решение:**
```bash
# 1. Проверить volumes
docker inspect bizcard-grafana | grep -A 10 Mounts

# 2. Проверить файлы
ls -la monitoring/grafana/dashboards/

# 3. Проверить формат JSON
cat monitoring/grafana/dashboards/my-dashboard.json | jq .

# 4. Проверить логи
docker logs bizcard-grafana | grep -E "error|ERROR"
```

### Проблема: "Dashboard title cannot be empty"

**Причина:** Неправильный формат JSON (с оберткой `{"dashboard": {...}}`)

**Решение:** Убрать обертку, оставить только содержимое `dashboard`.

### Проблема: Datasource не подключается

**Решение:**
```bash
# Проверить что Prometheus работает
docker ps | grep prometheus

# Проверить сеть
docker inspect bizcard-grafana | grep -A 5 Networks

# Должна быть сеть "monitoring"
```

---

## 📚 ПОЛЕЗНЫЕ ССЫЛКИ

- Grafana Provisioning: https://grafana.com/docs/grafana/latest/administration/provisioning/
- Dashboard JSON Model: https://grafana.com/docs/grafana/latest/dashboards/json-model/
- Prometheus Queries: https://prometheus.io/docs/prometheus/latest/querying/basics/

---

**Создано:** 2025-10-25  
**Версия:** 1.0  
**Статус:** ✅ **Дашборды настроены и работают**

