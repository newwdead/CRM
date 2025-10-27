# 📊 Руководство по мониторингу OCR v2.0 сервисов

## 🎯 Обзор

После интеграции OCR v2.0 в систему добавлены следующие новые сервисы:
- **PaddleOCR** - текстовое распознавание (внутри celery-worker)
- **LayoutLMv3** - AI классификация полей (внутри celery-worker)
- **MinIO** - S3 хранилище изображений
- **ValidatorService** - авто-коррекция данных (внутри backend)
- **Label Studio** - инструмент аннотации

---

## 🖥️ 1. Admin Panel UI (Самый простой способ)

### **Services Tab** - Docker контейнеры
**URL:** `https://ibbase.ru/admin?tab=services`

**Что показывает:**
- ✅ Статус всех Docker контейнеров (Running/Stopped/Unhealthy)
- 📊 CPU/Memory usage
- 🔄 Кнопки Restart для каждого сервиса
- 📜 Просмотр логов (кнопка "Logs")

**Как использовать:**
```
1. Откройте https://ibbase.ru/admin?tab=services
2. Проверьте статус:
   - backend: должен быть "healthy" (зеленый)
   - celery-worker: "running" или "healthy"
   - minio: "healthy"
   - label-studio: "running"
3. Если что-то "unhealthy" - нажмите "Restart"
4. Для логов - кнопка "Logs" рядом с контейнером
```

---

### **Settings Tab** - Статус интеграций
**URL:** `https://ibbase.ru/admin?tab=settings`

**Что показывает:**
- ✅ OCR v2.0 статус и конфигурация
- 🔌 Все интеграции (Telegram, WhatsApp, MinIO)
- 📊 Connection status для каждой интеграции
- ⚙️ Настройки (Configuration)

**Пример для OCR:**
```json
{
  "name": "OCR v2.0 Recognition",
  "status": "active",
  "configured": true,
  "config_summary": {
    "Version": "2.0 (PaddleOCR)",
    "AI Model": "LayoutLMv3 ✅",
    "Validator": "Auto-correct ✅",
    "Storage": "MinIO ✅",
    "Fallback": "Tesseract v1.0"
  }
}
```

---

### **Resources Tab** - URLs сервисов
**URL:** `https://ibbase.ru/admin?tab=resources`

**Что показывает:**
- 🔗 Все URLs сервисов (public + local)
- 🖥️ MinIO Console link
- 🏷️ Label Studio link
- 📦 Backend API docs

**Быстрый доступ:**
```
MinIO Console:   https://ibbase.ru:9001
Label Studio:    https://ibbase.ru:8081
Backend API:     https://ibbase.ru/api/docs
Prometheus:      http://localhost:9090
Grafana:         http://localhost:3001
```

---

## 🐳 2. Docker Commands (Командная строка)

### Статус всех контейнеров
```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Просмотр статуса
docker compose ps

# Пример вывода:
# NAME                    STATUS                  PORTS
# bizcard-backend         Up, healthy             8000
# bizcard-celery-worker   Up, health: starting    
# bizcard-minio           Up, healthy             9000-9001
```

### Логи конкретного сервиса
```bash
# Backend (FastAPI + OCR Manager)
docker compose logs -f backend

# Celery Worker (PaddleOCR + LayoutLMv3)
docker compose logs -f celery-worker

# MinIO (S3 Storage)
docker compose logs -f minio

# Label Studio
docker compose logs -f label-studio

# Только ошибки
docker compose logs --tail=50 backend | grep -i error

# OCR-специфичные логи
docker compose logs celery-worker | grep -E "(OCR|PaddleOCR|LayoutLM)"
```

### Последние 50 строк логов
```bash
docker compose logs --tail=50 celery-worker
```

### Мониторинг в реальном времени
```bash
# Следить за логами live
docker compose logs -f celery-worker

# Несколько сервисов одновременно
docker compose logs -f backend celery-worker minio
```

### Проверка использования ресурсов
```bash
# CPU и RAM для каждого контейнера
docker stats

# Только OCR-related контейнеры
docker stats bizcard-backend bizcard-celery-worker bizcard-minio
```

### Health check статус
```bash
# Детальная информация о контейнере
docker inspect bizcard-backend | grep -A 10 Health

# Проверка всех health checks
docker compose ps --format json | jq '.[] | {name: .Name, status: .Status, health: .Health}'
```

---

## 🔍 3. Backend API Endpoints

### Версия системы
```bash
curl http://localhost:8000/version | jq
```

**Ответ:**
```json
{
  "version": "6.0.0",
  "build": "production",
  "api_version": "v1",
  "security_update": "phase1-complete"
}
```

### Health check
```bash
curl http://localhost:8000/health
```

**Ответ:**
```json
{
  "status": "ok"
}
```

### Список всех сервисов
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/system/resources | jq
```

### Статус интеграций (включая OCR v2.0)
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/settings/integrations/status | jq '.integrations[] | select(.id=="ocr")'
```

**Ответ:**
```json
{
  "id": "ocr",
  "name": "OCR v2.0 Recognition",
  "enabled": true,
  "configured": true,
  "connection_ok": true,
  "config_summary": {
    "Version": "2.0 (PaddleOCR)",
    "AI Model": "LayoutLMv3 ✅",
    "Validator": "Auto-correct ✅",
    "Storage": "MinIO ✅"
  }
}
```

---

## 📦 4. MinIO Console (S3 Storage)

### Доступ
```
URL:      https://ibbase.ru:9001
Username: minioadmin
Password: minioadmin
```

### Что можно отслеживать:
1. **Buckets** - список корзин:
   - `business-cards` - загруженные визитки
   - `ocr-results` - результаты OCR
   - `training-data` - данные для обучения
   - `models` - сохраненные модели

2. **Metrics** - метрики хранилища:
   - Использование диска
   - Количество объектов
   - API requests/sec

3. **Monitoring** - мониторинг запросов:
   - GET/PUT операции
   - Ошибки
   - Latency

### Проверка через CLI
```bash
# Установить MinIO Client (mc)
curl https://dl.min.io/client/mc/release/linux-amd64/mc \
  --create-dirs \
  -o /usr/local/bin/mc
chmod +x /usr/local/bin/mc

# Настроить alias
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Список buckets
mc ls myminio

# Список файлов в bucket
mc ls myminio/business-cards

# Статистика bucket
mc du myminio/business-cards
```

---

## 🏷️ 5. Label Studio (Аннотация)

### Доступ
```
URL:      https://ibbase.ru:8081
Username: (создать при первом входе)
```

### Что можно отслеживать:
1. **Projects** - проекты аннотации
2. **Tasks** - количество аннотированных визиток
3. **Progress** - процент завершения
4. **Annotations** - качество разметки

### Проверка через API
```bash
# Health check
curl http://localhost:8081/health

# Список проектов (нужен API token)
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8081/api/projects
```

---

## 📊 6. Prometheus + Grafana (Метрики)

### Prometheus
```
URL: http://localhost:9090
```

**Основные метрики для OCR v2.0:**
```promql
# Backend requests
rate(http_requests_total[5m])

# OCR processing time
histogram_quantile(0.95, rate(ocr_processing_duration_seconds_bucket[5m]))

# Celery task queue length
celery_queue_length

# MinIO operations
rate(minio_s3_requests_total[5m])

# Memory usage
container_memory_usage_bytes{name=~"bizcard.*"}
```

### Grafana
```
URL:      http://localhost:3001
Username: admin
Password: admin (или ваш пароль)
```

**Dashboard для OCR v2.0:**
1. Import dashboard ID: `11074` (Docker monitoring)
2. Create custom dashboard:
   - OCR requests/sec
   - Processing time percentiles
   - Error rate
   - MinIO storage usage
   - Celery queue length

---

## ⚡ 7. Celery Monitoring (Задачи OCR)

### Celery Flower (Web UI)
```bash
# Установить Flower
docker compose exec celery-worker pip install flower

# Запустить Flower
docker compose exec celery-worker celery -A app.celery_app flower --port=5555
```

**Доступ:** `http://localhost:5555`

**Что показывает:**
- 🔄 Активные задачи OCR
- ✅ Успешные задачи
- ❌ Неудачные задачи
- ⏱️ Среднее время обработки
- 📊 Workers status

### Celery CLI
```bash
# Статус workers
docker compose exec celery-worker celery -A app.celery_app inspect active

# Зарегистрированные задачи
docker compose exec celery-worker celery -A app.celery_app inspect registered

# Статистика
docker compose exec celery-worker celery -A app.celery_app inspect stats
```

---

## 🔔 8. Автоматические алерты

### Создание скрипта мониторинга
```bash
#!/bin/bash
# /home/ubuntu/scripts/monitor_ocr.sh

echo "🔍 OCR v2.0 Services Status Check"
echo "=================================="

# Backend health
echo "Backend: $(curl -s http://localhost:8000/health | jq -r .status)"

# Celery worker
if docker compose ps celery-worker | grep -q "healthy\|running"; then
  echo "Celery:  ✅ Running"
else
  echo "Celery:  ❌ Down"
fi

# MinIO health
if docker compose ps minio | grep -q "healthy"; then
  echo "MinIO:   ✅ Healthy"
else
  echo "MinIO:   ❌ Down"
fi

# Disk space
echo "Disk:    $(df -h / | tail -1 | awk '{print $5}')"

# Recent OCR errors (last 10 minutes)
errors=$(docker compose logs --since 10m celery-worker | grep -c ERROR)
echo "Errors:  $errors in last 10 min"

if [ $errors -gt 10 ]; then
  echo "⚠️ WARNING: High error rate!"
fi
```

### Cron job для регулярных проверок
```bash
# Добавить в crontab
crontab -e

# Проверка каждые 5 минут
*/5 * * * * /home/ubuntu/scripts/monitor_ocr.sh >> /var/log/ocr_monitor.log 2>&1

# Ежедневный отчет в 9:00
0 9 * * * /home/ubuntu/scripts/ocr_daily_report.sh | mail -s "OCR v2.0 Daily Report" admin@ibbase.ru
```

---

## 🎯 9. Быстрая диагностика проблем

### Проблема: OCR не работает
```bash
# 1. Проверить статус celery-worker
docker compose ps celery-worker

# 2. Проверить логи на ошибки
docker compose logs --tail=100 celery-worker | grep -E "(ERROR|CRITICAL)"

# 3. Проверить загрузку моделей PaddleOCR
docker compose logs celery-worker | grep -i "paddle"

# 4. Проверить память
docker stats bizcard-celery-worker --no-stream

# 5. Перезапустить если нужно
docker compose restart celery-worker
```

### Проблема: MinIO недоступен
```bash
# 1. Проверить статус
docker compose ps minio

# 2. Проверить логи
docker compose logs --tail=50 minio

# 3. Проверить порты
netstat -tlnp | grep 9000

# 4. Тест доступности
curl -I http://localhost:9000/minio/health/live

# 5. Перезапустить
docker compose restart minio
```

### Проблема: Высокая нагрузка на CPU
```bash
# Проверить топ процессов в контейнере
docker compose exec celery-worker top

# Ограничить ресурсы в docker-compose.yml
services:
  celery-worker:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

---

## 📈 10. Key Performance Indicators (KPI)

### Метрики для отслеживания:

#### Backend API
- ✅ **Uptime:** > 99.9%
- ⏱️ **Response time:** < 200ms (p95)
- 📊 **Requests/sec:** мониторить тренд
- ❌ **Error rate:** < 0.1%

#### OCR Processing (Celery)
- ⏱️ **Processing time:** < 5 sec/card (p95)
- ✅ **Success rate:** > 95%
- 📊 **Queue length:** < 10
- 🔄 **Active workers:** 2 (по умолчанию)

#### MinIO Storage
- 💾 **Disk usage:** < 80%
- 📊 **Objects count:** мониторить рост
- ⏱️ **API latency:** < 100ms
- ✅ **Uptime:** > 99.9%

#### LayoutLMv3 AI
- 🎯 **Classification accuracy:** > 85%
- ⏱️ **Inference time:** < 2 sec
- 💾 **Model memory:** < 2GB

---

## 🚀 11. Dashboard URLs (Quick Access)

Создайте закладки для быстрого доступа:

```
📊 Admin Services:    https://ibbase.ru/admin?tab=services
⚙️ Admin Settings:    https://ibbase.ru/admin?tab=settings
🔗 Admin Resources:   https://ibbase.ru/admin?tab=resources

📦 MinIO Console:     https://ibbase.ru:9001
🏷️ Label Studio:      https://ibbase.ru:8081
📈 Prometheus:        http://localhost:9090
📊 Grafana:           http://localhost:3001
🌸 Flower (Celery):   http://localhost:5555 (если установлен)

📚 API Docs:          https://ibbase.ru/api/docs
🔍 API Redoc:         https://ibbase.ru/api/redoc
```

---

## 📝 12. Логирование

### Уровни логов для OCR v2.0

**Backend (`app/main.py`):**
```python
logger.info("🚀 OCR v2.0 initialized")     # Startup
logger.info("✅ OCR v2.0 completed")        # Success
logger.warning("⚠️ OCR v2.0 fallback")      # Fallback to v1.0
logger.error("❌ OCR v2.0 failed")          # Error
```

**Celery (`app/tasks.py`):**
```python
logger.info("Processing card with OCR v2.0")
logger.info("PaddleOCR: extracted 15 blocks")
logger.info("LayoutLMv3: classified 12 fields")
logger.info("Validator: corrected 3 fields")
logger.info("MinIO: saved to bucket business-cards")
```

### Просмотр логов по типам
```bash
# Все INFO логи
docker compose logs backend | grep INFO

# Только WARNING и ERROR
docker compose logs backend | grep -E "(WARNING|ERROR)"

# OCR-специфичные логи
docker compose logs celery-worker | grep "OCR"

# Статистика логов
docker compose logs --since 1h celery-worker | grep -c "OCR v2.0 completed"
```

---

## 🎓 Best Practices

### 1. Регулярные проверки (каждый день)
```bash
# Утренний чеклист
cd /home/ubuntu/fastapi-bizcard-crm-ready

# 1. Статус всех контейнеров
docker compose ps

# 2. Использование диска
df -h

# 3. Ошибки за последние 24 часа
docker compose logs --since 24h | grep -c ERROR

# 4. MinIO storage usage
mc du myminio/business-cards
```

### 2. Еженедельные задачи
- Проверить Grafana dashboards
- Проанализировать тренды метрик
- Проверить размер логов
- Обновить документацию если изменения

### 3. Ежемесячные задачи
- Ротация старых логов
- Cleanup MinIO old objects
- Обновление зависимостей
- Бэкап конфигураций

---

## 🔧 Troubleshooting Commands

### Полная перезагрузка OCR сервисов
```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Остановить все OCR-related
docker compose stop backend celery-worker minio

# Очистить старые контейнеры
docker compose rm -f backend celery-worker

# Пересобрать
docker compose build backend celery-worker

# Запустить
docker compose up -d backend celery-worker minio

# Проверить
docker compose ps
docker compose logs -f celery-worker
```

### Очистка кеша и временных файлов
```bash
# Docker cleanup
docker system prune -f

# Celery queue cleanup
docker compose exec redis redis-cli FLUSHDB

# Логи cleanup
docker compose logs --tail=0 > /dev/null
```

---

## 📞 Контакты и поддержка

**При проблемах проверить:**
1. Admin Panel → Services Tab
2. Docker logs
3. Prometheus metrics
4. MinIO Console

**Критические алерты:**
- Backend down → проверить `docker compose logs backend`
- Celery unhealthy → проверить память и CPU
- MinIO unavailable → проверить порты и disk space

**Полезные команды:**
```bash
# Быстрая диагностика
./scripts/monitor_ocr.sh

# Полная перезагрузка
docker compose restart

# Логи в реальном времени
docker compose logs -f
```

---

## ✅ Итоговый чеклист

- [ ] Admin Panel открывается: https://ibbase.ru/admin
- [ ] Services Tab показывает все контейнеры "healthy"
- [ ] MinIO Console доступен: https://ibbase.ru:9001
- [ ] Backend API работает: https://ibbase.ru/api/docs
- [ ] Prometheus собирает метрики: http://localhost:9090
- [ ] Grafana показывает дашборды: http://localhost:3001
- [ ] Celery worker обрабатывает задачи
- [ ] OCR v2.0 распознает визитки успешно

---

**Статус:** 📊 Полное руководство по мониторингу готово!  
**Дата:** 27 октября 2025  
**Версия:** v6.0.0 (OCR v2.0)

