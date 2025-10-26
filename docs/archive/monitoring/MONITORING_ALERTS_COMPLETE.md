# 🚨 MONITORING + ALERTS - ПОЛНОСТЬЮ НАСТРОЕНО!

**Дата:** 25 октября 2025  
**Статус:** ✅ ГОТОВО  
**URL:** https://monitoring.ibbase.ru  

---

## ✅ ЧТО СДЕЛАНО

### 1. ✅ Dashboards Автоматически Импортированы

**7 Dashboards загружены в Grafana:**

1. ✅ `1-system-overview.json` (10 панелей)
   - CPU, Memory, Disk, Network
   - Load Average, Disk I/O
   - System Stats

2. ✅ `2-docker-containers.json` (11 панелей)
   - Container CPU, Memory, Network, Disk
   - Running Containers
   - Container Status Table

3. ✅ `3-database-monitoring.json` (14 панелей)
   - PostgreSQL: Size, Connections, Transactions, Cache
   - Redis: Clients, Memory, Commands, Hit Rate

4. ✅ `4-application-monitoring.json` (14 панелей)
   - HTTP Requests, Response Time, Errors
   - Celery Tasks
   - OCR, Contacts Operations

5. ✅ `application-metrics.json`
6. ✅ `fastapi-crm-dashboard.json`
7. ✅ `system-overview.json`

---

### 2. ✅ Alert Rules Настроены

**4 Группы Alerts с 19 правилами:**

#### A. System Alerts (6 правил)

| Alert | Условие | Severity | For |
|-------|---------|----------|-----|
| **HighCPUUsage** | CPU > 80% | warning | 5m |
| **HighMemoryUsage** | RAM > 85% | warning | 5m |
| **CriticalMemoryUsage** | RAM > 95% | critical | 2m |
| **DiskSpaceLow** | Disk > 80% | warning | 10m |
| **DiskSpaceCritical** | Disk > 90% | critical | 5m |
| **HighSystemLoad** | Load > 2x CPU | warning | 10m |

#### B. Docker Alerts (3 правила)

| Alert | Условие | Severity | For |
|-------|---------|----------|-----|
| **ContainerHighCPU** | Container CPU > 80% | warning | 5m |
| **ContainerHighMemory** | Container RAM > 1GB | warning | 5m |
| **ContainerRestarted** | Container restarted | warning | 1m |

#### C. Database Alerts (6 правил)

| Alert | Условие | Severity | For |
|-------|---------|----------|-----|
| **PostgreSQLDown** | pg_up == 0 | critical | 1m |
| **PostgreSQLHighConnections** | Connections > 80% | warning | 5m |
| **PostgreSQLDeadlocks** | Deadlocks detected | warning | 1m |
| **PostgreSQLLowCacheHitRatio** | Cache < 90% | warning | 10m |
| **RedisDown** | redis_up == 0 | critical | 1m |
| **RedisHighMemory** | Memory > 80% | warning | 5m |

#### D. Application Alerts (4 правила)

| Alert | Условие | Severity | For |
|-------|---------|----------|-----|
| **ApplicationDown** | FastAPI down | critical | 1m |
| **HighErrorRate** | Errors > 5% | critical | 5m |
| **SlowResponseTime** | p95 > 2s | warning | 10m |
| **HighRequestRate** | > 100 req/s | warning | 5m |

---

## 📊 СТАТИСТИКА

```
✅ Dashboards:      7 импортированы
✅ Alert Rules:     19 активны (4 группы)
✅ Prometheus:      8 targets
✅ Exporters:       6 работают
✅ Метрики:         70+ собираются
```

---

## 🚀 КАК ИСПОЛЬЗОВАТЬ

### Dashboards:

1. Откройте Grafana:
   ```
   https://monitoring.ibbase.ru
   ```

2. Логин:
   ```
   Username: admin
   Password: admin
   ```

3. Dashboards уже импортированы!
   - Меню → Dashboards → Browse
   - Выберите нужный dashboard

---

### Alerts:

1. **В Prometheus:**
   ```
   http://localhost:9090/alerts
   ```
   - Все активные alerts
   - История срабатываний

2. **В Grafana:**
   - Меню → Alerting → Alert rules
   - Можно создать notification channels

---

## 🔧 КОНФИГУРАЦИЯ

### Prometheus:

**Файл:** `monitoring/prometheus.yml`
- 8 scrape jobs
- Alert rules включены

**Alert Rules:** `monitoring/alerts/alerts.yml`
- 4 группы
- 19 правил
- 225 строк

### Grafana:

**Provisioning:**
- `monitoring/grafana/provisioning/datasources/prometheus.yml`
- `monitoring/grafana/provisioning/dashboards/dashboards.yml`

**Dashboards:**
- `monitoring/grafana/dashboards/*.json` (7 файлов)

---

## 📈 ПРИМЕРЫ ALERTS

### Когда сработают:

**🟡 Warning Alerts:**
- CPU > 80% в течение 5 минут
- Memory > 85% в течение 5 минут
- Disk > 80% в течение 10 минут
- Error rate > 5% в течение 5 минут
- Response time > 2s в течение 10 минут

**🔴 Critical Alerts:**
- Memory > 95% в течение 2 минут
- Disk > 90% в течение 5 минут
- PostgreSQL down в течение 1 минуты
- Redis down в течение 1 минуты
- Application down в течение 1 минуты

---

## 🔗 БЫСТРЫЕ ССЫЛКИ

### Grafana:
- Dashboards: https://monitoring.ibbase.ru/dashboards
- Alerts: https://monitoring.ibbase.ru/alerting/list

### Prometheus:
- Targets: http://localhost:9090/targets
- Alerts: http://localhost:9090/alerts
- Rules: http://localhost:9090/rules
- Graph: http://localhost:9090/graph

---

## 🎯 ПРОВЕРКА ALERTS

### Тестирование:

```bash
# 1. Список всех alert rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].name'

# 2. Активные alerts
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts'

# 3. Статус targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | "\(.labels.job): \(.health)"'
```

---

## 📁 ФАЙЛЫ

```
monitoring/
├── prometheus.yml                    # Prometheus config ✅
├── alerts/
│   └── alerts.yml                   # 19 alert rules ✅
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml      # Auto datasource ✅
│   │   └── dashboards/
│   │       └── dashboards.yml       # Auto dashboards ✅
│   └── dashboards/
│       ├── 1-system-overview.json   ✅
│       ├── 2-docker-containers.json ✅
│       ├── 3-database-monitoring.json ✅
│       ├── 4-application-monitoring.json ✅
│       └── ... (7 total)
└── import_dashboards.sh             # Import script ✅
```

---

## 🔔 NOTIFICATION CHANNELS (Опционально)

### Для получения уведомлений:

1. **Email:**
   - Settings → Notification channels → New channel
   - Type: Email
   - Addresses: your@email.com

2. **Telegram:**
   - Type: Telegram
   - Bot Token: ...
   - Chat ID: ...

3. **Slack:**
   - Type: Slack
   - Webhook URL: ...

4. **Webhook:**
   - Type: Webhook
   - URL: https://your-webhook.com

---

## 🎯 NEXT STEPS

### Рекомендуемые действия:

1. ✅ **Проверить Dashboards**
   - Откройте https://monitoring.ibbase.ru
   - Просмотрите все 7 dashboards

2. ⏳ **Настроить Notification Channels**
   - Email для критичных alerts
   - Telegram для предупреждений

3. ⏳ **Кастомизировать Alerts**
   - Adjust thresholds для вашего окружения
   - Добавить бизнес-метрики

4. ⏳ **Создать Custom Dashboards**
   - Специфичные для вашего бизнеса
   - Объединить ключевые метрики

---

## ✅ ИТОГ

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   ✅ COMPREHENSIVE MONITORING + ALERTS                    ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

Dashboards:         ✅ 7 импортированы автоматически
Alert Rules:        ✅ 19 настроены (4 группы)
Prometheus:         ✅ 8 targets работают
Metrics:            ✅ 70+ собираются
Auto-refresh:       ✅ 30 секунд

STATUS:             🟢 ALL SYSTEMS OPERATIONAL
```

---

## 🚀 ГОТОВО!

**Откройте:** https://monitoring.ibbase.ru  
**Login:** admin / admin

**Все dashboards загружены!**  
**Все alerts настроены!**

---

**На русском! 🇷🇺**  
**Complete Monitoring Solution! 📊**  
**Stay Alert! 🚨**
