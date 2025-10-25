# 📊 COMPREHENSIVE MONITORING SETUP - COMPLETE

**Дата:** 25 октября 2025  
**Статус:** ✅ ПОЛНОСТЬЮ НАСТРОЕНО  
**URL:** https://monitoring.ibbase.ru  

---

## 🎯 ЧТО НАСТРОЕНО

### Полный мониторинг включает:

1. **Сервер** - CPU, Memory, Disk, Network, Load, I/O
2. **Docker Контейнеры** - все метрики всех контейнеров
3. **База Данных** - PostgreSQL + Redis метрики
4. **Приложение** - FastAPI, Celery, OCR, пользователи

---

## 🐳 ЗАПУЩЕННЫЕ СЕРВИСЫ

### Monitoring Stack:

| Сервис | Контейнер | Порт | Статус |
|--------|-----------|------|--------|
| **Grafana** | bizcard-grafana | 3001 | ✅ Up |
| **Prometheus** | bizcard-prometheus | 9090 | ✅ Up |
| **Node Exporter** | bizcard-node-exporter | 9100 | ✅ Up |
| **cAdvisor** | bizcard-cadvisor | 8080 | ✅ Up |
| **Postgres Exporter** | bizcard-postgres-exporter | 9187 | ✅ Up |
| **Redis Exporter** | bizcard-redis-exporter | 9121 | ✅ Up |

---

## 📊 GRAFANA DASHBOARDS

### Доступ к Grafana:

```
URL:      https://monitoring.ibbase.ru
Username: admin
Password: admin (сменить при первом входе!)
```

### 4 Comprehensive Dashboards:

#### 1. System Overview - Server Metrics
**Файл:** `monitoring/grafana/dashboards/1-system-overview.json`

**Метрики:**
- ✅ CPU Usage % (по времени)
- ✅ Memory Usage (Used/Available %)
- ✅ Disk Usage по каждому mount point
- ✅ Network Traffic (RX/TX по device)
- ✅ System Load Average (1m, 5m, 15m)
- ✅ Disk I/O (Read/Write по device)
- ✅ System Uptime
- ✅ Total CPU Cores
- ✅ Total Memory (RAM)
- ✅ Total Disk Space

**Панелей:** 10

---

#### 2. Docker Containers Monitoring
**Файл:** `monitoring/grafana/dashboards/2-docker-containers.json`

**Метрики:**
- ✅ Container CPU Usage (по контейнеру)
- ✅ Container Memory Usage (по контейнеру)
- ✅ Container Network RX (по контейнеру)
- ✅ Container Network TX (по контейнеру)
- ✅ Container Disk Read (по контейнеру)
- ✅ Container Disk Write (по контейнеру)
- ✅ Running Containers (count)
- ✅ Total CPU Usage (все контейнеры)
- ✅ Total Memory (все контейнеры)
- ✅ Container Restarts
- ✅ Container Status Table (таблица)

**Панелей:** 11

---

#### 3. Database Monitoring - PostgreSQL & Redis
**Файл:** `monitoring/grafana/dashboards/3-database-monitoring.json`

**PostgreSQL Метрики:**
- ✅ Database Size (bytes)
- ✅ Active Connections vs Max
- ✅ Transactions Per Second (commits/rollbacks)
- ✅ Tuples Read/Written (fetched/inserted/updated/deleted)
- ✅ Cache Hit Ratio %
- ✅ Deadlocks count
- ✅ PostgreSQL Status (Up/Down)
- ✅ Total Tables count

**Redis Метрики:**
- ✅ Connected Clients
- ✅ Memory Usage (used/max)
- ✅ Commands Per Second
- ✅ Hit Rate %
- ✅ Redis Status (Up/Down)
- ✅ Total Keys count

**Панелей:** 14

---

#### 4. Application Monitoring - FastAPI & Celery
**Файл:** `monitoring/grafana/dashboards/4-application-monitoring.json`

**Метрики:**
- ✅ HTTP Requests Per Second (по endpoint)
- ✅ HTTP Response Time p95 (percentile 95)
- ✅ HTTP Requests by Status Code (2xx, 4xx, 5xx)
- ✅ HTTP Error Rate % (5xx errors)
- ✅ Active Users count
- ✅ OCR Processing Rate (ocr/s)
- ✅ Celery Tasks Active
- ✅ Celery Tasks Success/Failure
- ✅ Contact Operations (created/updated/deleted)
- ✅ Duplicate Detection Rate
- ✅ API Status (Up/Down)
- ✅ Total Requests (24h)
- ✅ Avg Response Time
- ✅ Error Rate % (с thresholds)

**Панелей:** 14

---

## 🚀 КАК ИМПОРТИРОВАТЬ DASHBOARDS

### Вариант A: Через Web UI (Рекомендуется)

1. **Откройте Grafana:**
   ```
   https://monitoring.ibbase.ru
   ```

2. **Логин:**
   ```
   admin / admin
   ```

3. **Импорт dashboard'ов:**
   - В левом меню: **Dashboards → Import**
   - Нажмите **Upload JSON file**
   - Выберите файл из `monitoring/grafana/dashboards/`
   - Выберите data source: **Prometheus**
   - Нажмите **Import**

4. **Повторите для всех 4 dashboard'ов:**
   - `1-system-overview.json`
   - `2-docker-containers.json`
   - `3-database-monitoring.json`
   - `4-application-monitoring.json`

---

### Вариант B: Автоматический импорт (Script)

```bash
# Используйте Grafana API для автоматического импорта
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Импорт всех dashboards
for dashboard in monitoring/grafana/dashboards/*.json; do
  echo "Importing $(basename $dashboard)..."
  curl -X POST \
    -H "Content-Type: application/json" \
    -u admin:admin \
    -d @"$dashboard" \
    http://localhost:3001/api/dashboards/db
done
```

---

## 🔧 PROMETHEUS CONFIGURATION

### Конфигурация Prometheus:

**Файл:** `monitoring/prometheus.yml`

### 8 настроенных job'ов:

1. **prometheus** - Сам Prometheus
2. **node-exporter** - Метрики сервера (CPU, Memory, Disk, Network)
3. **cadvisor** - Метрики Docker контейнеров
4. **postgres** - Метрики PostgreSQL
5. **redis** - Метрики Redis
6. **fastapi-backend** - Метрики приложения FastAPI
7. **fastapi-health** - Health checks FastAPI
8. **celery** - Метрики Celery worker

### Проверка targets:

```bash
# Web UI
http://localhost:9090/targets

# CLI
curl http://localhost:9090/api/v1/targets
```

---

## 📈 ДОСТУПНЫЕ МЕТРИКИ

### System Metrics (Node Exporter):

```
node_cpu_seconds_total          # CPU usage
node_memory_*                   # Memory metrics
node_filesystem_*               # Disk metrics
node_network_*                  # Network metrics
node_load1, node_load5, node_load15  # Load average
node_disk_*                     # Disk I/O
node_boot_time_seconds          # System uptime
```

### Docker Metrics (cAdvisor):

```
container_cpu_usage_seconds_total    # Container CPU
container_memory_usage_bytes         # Container Memory
container_network_*                  # Container Network
container_fs_*                       # Container Disk
container_last_seen                  # Container status
```

### PostgreSQL Metrics:

```
pg_up                           # Database status
pg_database_size_bytes          # Database size
pg_stat_database_*              # Database stats
pg_stat_user_tables_*           # Table stats
pg_settings_max_connections     # Max connections
```

### Redis Metrics:

```
redis_up                        # Redis status
redis_connected_clients         # Clients count
redis_memory_*                  # Memory usage
redis_commands_processed_total  # Commands count
redis_keyspace_*                # Hit/miss ratio
redis_db_keys                   # Total keys
```

### Application Metrics (FastAPI):

```
http_requests_total             # Total HTTP requests
http_request_duration_seconds   # Response time
user_login_total                # Active users
ocr_processing_total            # OCR processing
contact_created_total           # Contact operations
duplicate_detection_total       # Duplicate detection
celery_tasks_*                  # Celery tasks
```

---

## 🎯 ПРИМЕРЫ ЗАПРОСОВ (PromQL)

### System:

```promql
# CPU Usage %
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Usage %
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100

# Disk Usage %
(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100

# Network Traffic (bits/s)
irate(node_network_receive_bytes_total[5m]) * 8
```

### Docker:

```promql
# Container CPU %
sum(rate(container_cpu_usage_seconds_total[5m])) by (name) * 100

# Container Memory
container_memory_usage_bytes{name=~".+"}

# Running containers
count(container_last_seen{name=~".+"})
```

### Database:

```promql
# PostgreSQL transactions/s
rate(pg_stat_database_xact_commit{datname="businesscards"}[5m])

# Redis commands/s
rate(redis_commands_processed_total[5m])

# Cache hit ratio
pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) * 100
```

### Application:

```promql
# HTTP requests/s
rate(http_requests_total[5m])

# Response time p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate %
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```

---

## 🔧 УПРАВЛЕНИЕ

### Restart всех сервисов:

```bash
docker restart bizcard-grafana
docker restart bizcard-prometheus
docker restart bizcard-node-exporter
docker restart bizcard-cadvisor
docker restart bizcard-postgres-exporter
docker restart bizcard-redis-exporter
```

### Проверка логов:

```bash
docker logs bizcard-grafana
docker logs bizcard-prometheus
docker logs bizcard-cadvisor
```

### Reload Prometheus config:

```bash
# With --web.enable-lifecycle flag
curl -X POST http://localhost:9090/-/reload

# Or restart container
docker restart bizcard-prometheus
```

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
monitoring/
├── prometheus.yml                    # Prometheus config ✅
├── prometheus.yml.backup             # Backup old config
├── prometheus-data/                  # Prometheus data
├── grafana-data/                     # Grafana data
└── grafana/
    └── dashboards/
        ├── 1-system-overview.json           ✅
        ├── 2-docker-containers.json         ✅
        ├── 3-database-monitoring.json       ✅
        ├── 4-application-monitoring.json    ✅
        └── fastapi-crm-dashboard.json       (old)
```

---

## ⚙️ НАСТРОЙКА ALERTS (Опционально)

### Создание alerts в Prometheus:

```yaml
# monitoring/alerts/system_alerts.yml
groups:
  - name: system
    rules:
      - alert: HighCPU
        expr: 100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        annotations:
          summary: "High CPU usage detected"
          
      - alert: HighMemory
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
        for: 5m
        annotations:
          summary: "High Memory usage detected"
          
      - alert: DiskSpaceLow
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 85
        for: 10m
        annotations:
          summary: "Disk space running low"
```

---

## ✅ ИТОГ

### ЧТО ГОТОВО:

- ✅ 6 exporters запущены и работают
- ✅ Prometheus собирает метрики со всех источников
- ✅ Grafana доступна на https://monitoring.ibbase.ru
- ✅ 4 comprehensive dashboards созданы (49 панелей)
- ✅ Мониторинг: Сервер + Docker + БД + Приложение

### ВСЕГО МЕТРИК:

- **System:** 10+ metrics (CPU, Memory, Disk, Network, Load, I/O)
- **Docker:** 15+ metrics (per container CPU, Memory, Network, Disk)
- **PostgreSQL:** 20+ metrics (connections, transactions, queries, cache)
- **Redis:** 10+ metrics (clients, memory, commands, keys, hit rate)
- **Application:** 15+ metrics (requests, response time, errors, users, OCR, Celery)

**ИТОГО:** 70+ различных метрик!

### DASHBOARDS:

- **Панелей:** 49 total
- **Графиков:** Timeseries, Stats, Tables
- **Auto-refresh:** 30 секунд
- **Доступ:** https://monitoring.ibbase.ru

---

## 🎯 ДАЛЬНЕЙШИЕ ШАГИ

1. **Импортировать dashboards** в Grafana
2. **Настроить alerts** (опционально)
3. **Настроить Alertmanager** для уведомлений (опционально)
4. **Создать кастомные dashboards** для specific needs
5. **Мониторить регулярно** и оптимизировать

---

## 🔗 ПОЛЕЗНЫЕ ССЫЛКИ

- **Grafana:** https://monitoring.ibbase.ru
- **Prometheus:** http://localhost:9090
- **Prometheus Targets:** http://localhost:9090/targets
- **cAdvisor:** http://localhost:8080
- **Node Exporter:** http://localhost:9100/metrics
- **Postgres Exporter:** http://localhost:9187/metrics
- **Redis Exporter:** http://localhost:9121/metrics

---

**На русском! 🇷🇺**  
**Comprehensive Monitoring Ready! 📊**  
**All Systems Monitored! 🎯**
