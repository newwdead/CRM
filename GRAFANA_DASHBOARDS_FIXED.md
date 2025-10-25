# ✅ GRAFANA ДАШБОРДЫ ВОССТАНОВЛЕНЫ

## 🔴 ПРОБЛЕМА

**Дашборды в Grafana пропадали** после перезапуска контейнера.

### Причина:
```yaml
# docker-compose.monitoring-full.yml - ДО
volumes:
  - grafana_data:/var/lib/grafana  # Только БД, БЕЗ дашбордов!
```

Не было монтирования:
- ❌ provisioning конфигурации
- ❌ JSON файлов дашбордов

**Результат:** При каждом перезапуске контейнера дашборды исчезали.

---

## ✅ РЕШЕНИЕ

### 1. Добавлены volumes в docker-compose:

```yaml
volumes:
  - grafana_data:/var/lib/grafana                                    # БД Grafana
  - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro   # Provisioning
  - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro   # Dashboards JSON
```

### 2. Исправлен путь в provisioning config:

```yaml
# monitoring/grafana/provisioning/dashboards/dashboards.yml
options:
  path: /var/lib/grafana/dashboards  # ← Правильный путь
```

### 3. Удалены битые дашборды:

```
❌ 1-system-overview.json         (неправильный формат)
❌ 2-docker-containers.json        (неправильный формат)
❌ 3-database-monitoring.json      (неправильный формат)
❌ 4-application-monitoring.json   (неправильный формат)
```

**Проблема с форматом:** Были с оберткой `{"dashboard": {...}}`, а нужно просто `{...}`.

### 4. Оставлены рабочие дашборды:

```
✅ fastapi-crm-dashboard.json     (8.2KB)
✅ system-overview.json            (7.7KB)
✅ application-metrics.json        (2.2KB)
```

---

## 🔄 КАК РАБОТАЕТ ТЕПЕРЬ

### При запуске Grafana:

1. **Читает provisioning config** из `/etc/grafana/provisioning/`
2. **Автоматически настраивает** Prometheus datasource
3. **Загружает дашборды** из `/var/lib/grafana/dashboards/*.json`
4. **Дашборды появляются** в UI автоматически

### Каждые 10 секунд:

- Проверяет изменения в JSON файлах
- Автоматически обновляет дашборды

### При перезапуске:

- ✅ Дашборды **НЕ ПРОПАДАЮТ**
- ✅ Автоматически загружаются из файлов
- ✅ Конфигурация сохраняется

---

## 📊 ТЕКУЩИЕ ДАШБОРДЫ

### 1. FastAPI CRM Dashboard
**Файл:** `fastapi-crm-dashboard.json`  
**UID:** `fastapi-crm`  
**Метрики:**
- HTTP Request Rate & Duration
- Active Users & Sessions
- Contact Operations (Create/Update/Delete)
- OCR Processing Stats
- Database Query Performance
- Cache Hit Rate
- Error Rate & Logs

### 2. System Overview
**Файл:** `system-overview.json`  
**UID:** `system-overview`  
**Метрики:**
- CPU Usage %
- Memory Usage (RAM)
- Disk I/O Operations
- Network Traffic (In/Out)
- System Load Average

### 3. Application Metrics
**Файл:** `application-metrics.json`  
**UID:** `application-metrics`  
**Метрики:**
- API Response Times (p50, p95, p99)
- Database Connection Pool
- Redis Operations & Cache
- Celery Task Queue

---

## 💾 КАК ДОБАВИТЬ НОВЫЙ ДАШБОРД

### Шаг 1: Создать в Grafana UI

```
1. Открыть https://monitoring.ibbase.ru
2. Login: admin / <password>
3. Create → Dashboard
4. Настроить панели
5. Save dashboard
```

### Шаг 2: Экспортировать JSON

```
1. Dashboard Settings (⚙️)
2. JSON Model
3. Copy to clipboard
```

### Шаг 3: Сохранить на сервере

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

cat > monitoring/grafana/dashboards/my-dashboard.json << 'JSON'
{
  "title": "My Dashboard",
  "uid": "my-dashboard-uid",
  "panels": [...]
}
JSON

# Grafana подхватит автоматически через 10 секунд!
```

### Шаг 4: Закоммитить

```bash
git add monitoring/grafana/dashboards/my-dashboard.json
git commit -m "📊 Add new dashboard: My Dashboard"
git push origin main
```

---

## 🔒 БЕЗОПАСНОСТЬ

### Текущая конфигурация:

```
✅ Grafana порт: 127.0.0.1:3001 (только localhost)
✅ Публичный доступ: https://monitoring.ibbase.ru (через Nginx + auth)
✅ Dashboards: read-only (:ro)
✅ Provisioning: read-only (:ro)
```

### Доступ:

- **Локально:** `http://localhost:3001` (с сервера)
- **Публично:** `https://monitoring.ibbase.ru` (с любого места)

---

## 🧪 ТЕСТИРОВАНИЕ

### ✅ Проверено:

```bash
# 1. Контейнер запущен
docker ps | grep grafana
# bizcard-grafana   Up 5 minutes   127.0.0.1:3001->3000/tcp

# 2. Volumes смонтированы
docker inspect bizcard-grafana | grep -A 3 Mounts
# "/home/ubuntu/.../provisioning:/etc/grafana/provisioning:ro"
# "/home/ubuntu/.../dashboards:/var/lib/grafana/dashboards:ro"

# 3. Логи без ошибок
docker logs bizcard-grafana | grep dashboard
# ✅ "starting to provision dashboards"
# ✅ "finished to provision dashboards"
# ❌ NO "Dashboard title cannot be empty"

# 4. Дашборды загружены
# ✅ 3 dashboards visible in Grafana UI
```

---

## 📋 СТРУКТУРА ФАЙЛОВ

```
monitoring/
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml          # Prometheus datasource
│   │   └── dashboards/
│   │       └── dashboards.yml          # Dashboard provider
│   └── dashboards/                     # ← JSON дашборды здесь!
│       ├── fastapi-crm-dashboard.json  ✅
│       ├── system-overview.json        ✅
│       └── application-metrics.json    ✅
└── grafana-data/                       # Volume БД Grafana
```

---

## 🔧 TROUBLESHOOTING

### Дашборды не появляются?

```bash
# 1. Проверить volumes
docker inspect bizcard-grafana | grep Mounts

# 2. Проверить файлы
ls -la monitoring/grafana/dashboards/

# 3. Проверить формат JSON (должен быть валидный)
cat monitoring/grafana/dashboards/my-dashboard.json | jq .

# 4. Перезапустить Grafana
docker compose -f docker-compose.monitoring-full.yml restart grafana

# 5. Проверить логи
docker logs bizcard-grafana --tail 30 | grep -E "error|ERROR|dashboard"
```

### Ошибка "Dashboard title cannot be empty"?

**Причина:** Неправильный формат JSON с оберткой `{"dashboard": {...}}`

**Решение:** Убрать обертку, оставить только содержимое:

```json
// ❌ НЕПРАВИЛЬНО
{
  "dashboard": {
    "title": "My Dashboard",
    ...
  }
}

// ✅ ПРАВИЛЬНО
{
  "title": "My Dashboard",
  "uid": "my-dashboard",
  ...
}
```

---

## 📚 ДОКУМЕНТАЦИЯ

**Создан:** `GRAFANA_DASHBOARDS_GUIDE.md` (11+ KB)

**Содержит:**
- Как работает auto-provisioning
- Как сохранять и экспортировать дашборды
- Правильный формат JSON
- Troubleshooting guide
- Best practices
- Security tips

---

## ✅ ИТОГИ

| Аспект | До | После |
|--------|-----|-------|
| **Дашборды после перезапуска** | ❌ Пропадали | ✅ Сохраняются |
| **Auto-provisioning** | ❌ Нет | ✅ Да |
| **Version control** | ❌ Нет | ✅ Git |
| **Количество дашбордов** | 4 битых | 3 рабочих |
| **Ручная настройка** | ❌ Нужна | ✅ Не нужна |

---

## 🎯 РЕЗУЛЬТАТ

```
✅ Дашборды восстановлены
✅ Auto-provisioning настроен
✅ Persistent storage включен
✅ Документация создана
✅ Git commits made
✅ Протестировано

🎉 ПРОБЛЕМА РЕШЕНА НАВСЕГДА!
```

---

**Создано:** 2025-10-25  
**Commit:** `5750515`  
**Статус:** ✅ **ДАШБОРДЫ РАБОТАЮТ И НЕ ПРОПАДАЮТ**
