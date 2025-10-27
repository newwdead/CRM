# ⚡ Quick Monitoring Reference - OCR v2.0

## 🎯 1-минутная проверка системы

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Быстрая проверка всех сервисов
docker compose ps backend celery-worker minio

# Версия и статус
curl -s http://localhost:8000/version | jq
curl -s http://localhost:8000/health
```

---

## 📊 Основные способы мониторинга

### 1️⃣ **Admin Panel** (самый простой!)
```
🔗 URL: https://ibbase.ru/admin?tab=services

Показывает:
✅ Статус всех Docker контейнеров
📊 CPU/Memory usage  
🔄 Кнопки Restart
📜 Просмотр логов

Время: 10 секунд
```

### 2️⃣ **Docker Commands**
```bash
# Статус
docker compose ps

# Логи (live)
docker compose logs -f celery-worker

# Ресурсы
docker stats --no-stream

Время: 30 секунд
```

### 3️⃣ **MinIO Console**
```
🔗 URL: https://ibbase.ru:9001
👤 Login: minioadmin / minioadmin

Показывает:
📦 Загруженные визитки
📊 Disk usage
⚡ API requests

Время: 1 минута
```

### 4️⃣ **Prometheus + Grafana**
```
🔗 Prometheus: http://localhost:9090
🔗 Grafana:    http://localhost:3001

Показывает:
📈 Метрики в реальном времени
⏱️ Response times
❌ Error rates

Время: 2 минуты
```

---

## 🚨 Быстрая диагностика проблем

### Проблема: OCR не работает
```bash
# 1. Проверить celery-worker
docker compose ps celery-worker

# 2. Логи
docker compose logs --tail=50 celery-worker | grep ERROR

# 3. Перезапустить
docker compose restart celery-worker
```

### Проблема: MinIO недоступен
```bash
# 1. Статус
docker compose ps minio

# 2. Тест
curl -I http://localhost:9000/minio/health/live

# 3. Перезапустить
docker compose restart minio
```

### Проблема: Backend тормозит
```bash
# Проверить ресурсы
docker stats bizcard-backend --no-stream

# Логи
docker compose logs --tail=100 backend | grep ERROR

# Перезапустить
docker compose restart backend
```

---

## 📱 Daily Commands (ежедневные команды)

### Утренняя проверка (1 минута)
```bash
#!/bin/bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

echo "🌅 Morning Check - OCR v2.0"
echo "=========================="

# Статус контейнеров
docker compose ps --format "{{.Name}}: {{.Status}}"

# Ошибки за ночь
errors=$(docker compose logs --since 12h | grep -c ERROR)
echo "Errors last 12h: $errors"

# Disk space
df -h / | tail -1 | awk '{print "Disk: " $5 " used"}'

echo "✅ Check complete!"
```

### Вечерняя проверка (30 секунд)
```bash
# Обработано визиток за день
docker compose logs --since 24h celery-worker | grep -c "OCR completed"

# Использование MinIO
docker compose exec minio du -sh /data
```

---

## 🎯 Key Metrics (что отслеживать)

### ✅ Нормальные значения:
```
Backend:      Status: healthy, CPU < 50%
Celery:       Status: running, Memory < 2GB
MinIO:        Status: healthy, Disk < 80%
Redis:        Status: healthy, Memory < 512MB
```

### ⚠️ Тревожные значения:
```
Backend:      CPU > 80%, много ERROR в логах
Celery:       Status: unhealthy, Memory > 4GB
MinIO:        Disk > 90%, много failed requests
Redis:        Memory > 1GB, connection errors
```

---

## 📞 Контакты и URLs

### Admin Panel
```
Services:  https://ibbase.ru/admin?tab=services
Settings:  https://ibbase.ru/admin?tab=settings
Resources: https://ibbase.ru/admin?tab=resources
```

### Monitoring Tools
```
MinIO:      https://ibbase.ru:9001
Label:      https://ibbase.ru:8081
Prometheus: http://localhost:9090
Grafana:    http://localhost:3001
API Docs:   https://ibbase.ru/api/docs
```

### Logs Locations
```
Backend:    docker compose logs backend
Celery:     docker compose logs celery-worker
MinIO:      docker compose logs minio
All:        docker compose logs
```

---

## 🔧 Emergency Commands

### Полная перезагрузка
```bash
docker compose restart
```

### Только OCR сервисы
```bash
docker compose restart backend celery-worker
```

### Очистка и rebuild (если ничего не помогает)
```bash
docker compose down
docker compose build --no-cache backend celery-worker
docker compose up -d
```

---

## 📊 Status Check Script

Создайте файл `/home/ubuntu/check_ocr.sh`:

```bash
#!/bin/bash
# Quick OCR v2.0 status check

echo "🔍 OCR v2.0 Status Check"
echo "======================="
echo ""

# 1. Containers
echo "1. Docker Containers:"
docker compose ps --format "  {{.Name}}: {{.Status}}" | grep -E "(backend|celery|minio)"
echo ""

# 2. Version
echo "2. Backend Version:"
version=$(curl -s http://localhost:8000/version | jq -r .version)
echo "  v$version"
echo ""

# 3. Health
echo "3. Health Check:"
health=$(curl -s http://localhost:8000/health | jq -r .status)
echo "  Status: $health"
echo ""

# 4. Recent errors
echo "4. Recent Errors (last 1h):"
errors=$(docker compose logs --since 1h | grep -c ERROR)
echo "  Count: $errors"
echo ""

# 5. Disk space
echo "5. Disk Space:"
df -h / | tail -1 | awk '{print "  Used: " $5}'
echo ""

echo "✅ Check complete!"
```

Использование:
```bash
chmod +x /home/ubuntu/check_ocr.sh
/home/ubuntu/check_ocr.sh
```

---

## ⏰ Automated Monitoring (Автоматизация)

### Cron Job для ежедневного отчета
```bash
# Добавить в crontab
crontab -e

# Каждый день в 9:00
0 9 * * * /home/ubuntu/check_ocr.sh | mail -s "OCR Daily Report" admin@ibbase.ru

# Каждые 5 минут - проверка здоровья
*/5 * * * * docker compose ps | grep -E "(unhealthy|Exited)" && echo "Alert: Service down!" | mail -s "OCR Alert" admin@ibbase.ru
```

---

## 💡 Pro Tips

### 1. Создайте alias для быстрого доступа
```bash
# Добавьте в ~/.bashrc
alias ocr-status='cd /home/ubuntu/fastapi-bizcard-crm-ready && docker compose ps'
alias ocr-logs='cd /home/ubuntu/fastapi-bizcard-crm-ready && docker compose logs -f celery-worker'
alias ocr-restart='cd /home/ubuntu/fastapi-bizcard-crm-ready && docker compose restart backend celery-worker'

# Применить
source ~/.bashrc

# Теперь можно использовать:
ocr-status
ocr-logs
ocr-restart
```

### 2. Watch mode для мониторинга
```bash
# Автообновление каждые 2 секунды
watch -n 2 'docker compose ps'

# CPU/Memory в реальном времени
watch -n 1 'docker stats --no-stream'
```

### 3. Быстрый поиск ошибок
```bash
# Последние 10 ошибок с временем
docker compose logs --since 1h | grep ERROR | tail -10

# Группировка ошибок по типу
docker compose logs --since 24h | grep ERROR | cut -d: -f3- | sort | uniq -c | sort -rn
```

---

## 📖 Дополнительная документация

Для детального мониторинга смотрите:
- 📄 `MONITORING_GUIDE_OCR_V2.md` - полное руководство
- 📄 `OCR_V2_DOCUMENTATION.md` - техническая документация
- 📄 `OCR_V2_ADMIN_INTEGRATION_COMPLETE.md` - интеграция с Admin UI

---

**Статус:** ⚡ Quick Reference готов к использованию!  
**Дата:** 27 октября 2025  
**Версия:** v6.0.0 (OCR v2.0)

