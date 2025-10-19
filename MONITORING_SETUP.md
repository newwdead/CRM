# 📊 Monitoring Setup - BizCard CRM

## Overview

BizCard CRM включает полный стек мониторинга на базе **Prometheus + Grafana** для отслеживания производительности системы, приложения и баз данных в режиме реального времени.

## 🎯 Что Мониторим

### System Metrics (Node Exporter)
- ✅ **CPU** - загрузка процессора по ядрам
- ✅ **Memory** - использование RAM, swap, buffers/cache
- ✅ **Disk** - использование дискового пространства, I/O
- ✅ **Network** - входящий/исходящий трафик, ошибки

### Application Metrics (FastAPI)
- ✅ **HTTP Requests** - количество запросов в секунду
- ✅ **Response Time** - 50th, 95th, 99th percentiles
- ✅ **OCR Processing** - время обработки по провайдерам
- ✅ **OCR Success Rate** - успешность распознавания
- ✅ **Contacts** - общее количество и скорость создания
- ✅ **Users** - количество пользователей
- ✅ **Auth Attempts** - успешные/неуспешные попытки входа

### Database Metrics (PostgreSQL Exporter)
- ✅ **Connections** - активные подключения
- ✅ **Query Performance** - время выполнения запросов
- ✅ **Database Size** - размер БД и таблиц
- ✅ **Cache Hit Ratio** - эффективность кэша

### Container Metrics (cAdvisor)
- ✅ **Container CPU** - использование CPU контейнерами
- ✅ **Container Memory** - использование памяти
- ✅ **Container Network** - сетевой трафик
- ✅ **Container Restarts** - перезапуски контейнеров

---

## 🚀 Быстрый Старт

### 1. Запуск Мониторинга (Локально)

```bash
# Запустить основную систему + мониторинг
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Проверить статус
docker compose ps

# Проверить логи
docker compose logs -f prometheus grafana
```

### 2. Доступ к Интерфейсам

| Сервис | URL | Credentials |
|--------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Node Exporter** | http://localhost:9100/metrics | - |
| **cAdvisor** | http://localhost:8080 | - |
| **FastAPI Metrics** | http://localhost:8000/metrics | - |

### 3. Просмотр Дашбордов

1. Откройте Grafana: http://localhost:3001
2. Войдите с credentials: `admin` / `admin`
3. Смените пароль при первом входе
4. Перейдите в **Dashboards** → **BizCard CRM**
5. Выберите дашборд:
   - **System Overview** - системные метрики
   - **Application Metrics** - метрики приложения

---

## 🌐 Развертывание в VK Cloud

### Предварительные Требования

- VK Cloud аккаунт
- Созданная виртуальная машина (рекомендуется: 2 vCPU, 4GB RAM)
- Docker и Docker Compose установлены
- Открытые порты: 80, 443, 3000, 3001, 8000, 9090

### Шаг 1: Подготовка VM в VK Cloud

```bash
# SSH на сервер
ssh ubuntu@your-vk-cloud-ip

# Установить Docker (если еще не установлен)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установить Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перелогиниться для применения прав Docker
exit
ssh ubuntu@your-vk-cloud-ip
```

### Шаг 2: Клонировать Проект

```bash
# Клонировать репозиторий
git clone https://github.com/newwdead/CRM.git
cd CRM

# Создать .env файл
cp .env.example .env
nano .env  # Настроить переменные окружения
```

### Шаг 3: Настроить Prometheus для VK Cloud

Отредактируйте `monitoring/prometheus/prometheus.yml`:

```yaml
global:
  external_labels:
    cluster: 'bizcard-crm-vkcloud'
    environment: 'production'
    datacenter: 'msk'  # Ваш дата-центр VK Cloud

# Опционально: настройка remote write для долговременного хранения
# remote_write:
#   - url: "https://prometheus.vk.cloud/api/v1/write"
#     basic_auth:
#       username: "your-vk-cloud-username"
#       password: "your-vk-cloud-password"
```

### Шаг 4: Настроить Grafana для VK Cloud

Отредактируйте `docker-compose.monitoring.yml`:

```yaml
grafana:
  environment:
    # Установите URL вашего сервера
    - GF_SERVER_ROOT_URL=https://monitoring.your-domain.com
    - GF_SERVER_DOMAIN=monitoring.your-domain.com
    
    # Смените дефолтный пароль!
    - GF_SECURITY_ADMIN_PASSWORD=your-strong-password
    
    # Настройка SMTP для алертов (опционально)
    - GF_SMTP_ENABLED=true
    - GF_SMTP_HOST=smtp.vk.cloud:587
    - GF_SMTP_USER=alerts@your-domain.com
    - GF_SMTP_PASSWORD=your-smtp-password
    - GF_SMTP_FROM_ADDRESS=alerts@your-domain.com
```

### Шаг 5: Настроить Firewall в VK Cloud

В консоли VK Cloud откройте порты для Security Group:

| Порт | Протокол | Источник | Назначение |
|------|----------|----------|------------|
| 22 | TCP | Your IP | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 3000 | TCP | Your IP | Frontend (dev) |
| 3001 | TCP | Your IP | Grafana |
| 8000 | TCP | Your IP | Backend API |
| 9090 | TCP | Your IP | Prometheus |

⚠️ **Важно**: В production оставьте открытыми только 80 и 443!

### Шаг 6: Запуск

```bash
# Production запуск
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               -f docker-compose.monitoring.yml \
               up -d --build

# Проверить статус
docker compose ps

# Проверить логи
docker compose logs -f
```

### Шаг 7: Настроить HTTPS (Let's Encrypt)

```bash
# Установить Certbot
sudo apt-get update
sudo apt-get install certbot

# Получить сертификат
sudo certbot certonly --standalone -d your-domain.com -d monitoring.your-domain.com

# Обновить nginx конфигурацию для использования сертификатов
# См. SSL_SETUP.md для деталей
```

### Шаг 8: Настроить Reverse Proxy для Grafana

Создайте nginx конфигурацию для проксирования Grafana:

```nginx
# /etc/nginx/sites-available/monitoring
server {
    listen 443 ssl http2;
    server_name monitoring.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📊 Использование Grafana

### Создание Алертов

1. Откройте Grafana → **Alerting** → **Alert rules**
2. Нажмите **New alert rule**
3. Настройте условия (например: CPU > 80% на 5 минут)
4. Настройте notification channel (Email, Telegram, Slack)
5. Сохраните правило

### Пример Alert Rule для CPU

```yaml
name: High CPU Usage
condition:
  query: avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100
  threshold: 80
  duration: 5m
notification:
  channel: email
  message: "CPU usage is above 80% for 5 minutes"
```

### Добавление Telegram Notifications

1. Создайте Telegram бота через @BotFather
2. Получите Bot Token
3. В Grafana: **Alerting** → **Contact points** → **New contact point**
4. Выберите **Telegram**
5. Введите Bot Token и Chat ID
6. Сохраните и протестируйте

---

## 🔧 Custom Метрики

### Добавление Новых Метрик в Backend

Отредактируйте `backend/app/main.py`:

```python
from prometheus_client import Counter, Gauge, Histogram

# Создайте метрику
my_custom_counter = Counter(
    'my_custom_metric_total',
    'Description of my metric',
    ['label1', 'label2']
)

# Используйте в коде
@app.post('/my-endpoint/')
def my_endpoint():
    my_custom_counter.labels(label1='value1', label2='value2').inc()
    # ... your code ...
```

### Просмотр Метрик

```bash
# Просмотр всех метрик FastAPI
curl http://localhost:8000/metrics

# Фильтр по конкретной метрике
curl http://localhost:8000/metrics | grep ocr_processing
```

---

## 📈 Рекомендуемые Алерты

### Critical Alerts (Требуют немедленного внимания)

- ❌ **Backend Down** - сервис недоступен > 1 минуты
- ❌ **Database Down** - БД недоступна > 1 минуты
- ❌ **Disk Space < 10%** - критически мало места
- ❌ **Memory Usage > 95%** - критическая нехватка памяти

### Warning Alerts (Требуют проверки)

- ⚠️ **CPU Usage > 80%** - высокая нагрузка > 5 минут
- ⚠️ **Memory Usage > 85%** - высокое использование памяти
- ⚠️ **Disk Space < 20%** - заканчивается место
- ⚠️ **High OCR Failure Rate** - > 20% ошибок OCR
- ⚠️ **Slow Response Time** - 95th percentile > 2 секунд
- ⚠️ **Failed Login Attempts** - > 10 попыток/сек

---

## 🔍 Troubleshooting

### Prometheus не собирает метрики

**Проблема**: Prometheus показывает targets как "DOWN"

**Решение**:
```bash
# Проверить доступность метрик
curl http://localhost:8000/metrics

# Проверить конфигурацию Prometheus
docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Перезапустить Prometheus
docker compose restart prometheus
```

### Grafana не показывает данные

**Проблема**: Дашборды пустые или показывают "No data"

**Решение**:
1. Проверьте подключение к Prometheus: Configuration → Data Sources
2. Проверьте что Prometheus собирает данные: http://localhost:9090/targets
3. Проверьте запросы в дашборде: Edit Panel → Query
4. Проверьте временной диапазон (Time range)

### High Memory Usage

**Проблема**: Prometheus/Grafana потребляют много памяти

**Решение**:
```yaml
# Ограничить retention в prometheus.yml
global:
  storage:
    tsdb:
      retention.time: 15d  # Хранить только 15 дней
      retention.size: 10GB # Максимум 10GB
```

### Slow Queries

**Проблема**: Запросы к Prometheus медленные

**Решение**:
- Используйте rate() вместо irate() где возможно
- Увеличьте scrape_interval для менее критичных метрик
- Используйте recording rules для предвычисления сложных запросов

---

## 🎯 Best Practices

### Производительность

1. **Оптимизация Retention**
   - Храните метрики только необходимое время (15-30 дней)
   - Используйте remote_write для долговременного хранения

2. **Scrape Interval**
   - Критичные метрики: 10-15 секунд
   - Обычные метрики: 30 секунд
   - Системные метрики: 60 секунд

3. **Cardinality**
   - Избегайте высокой cardinality в labels
   - Не используйте user IDs, email как labels
   - Используйте ограниченное количество значений

### Безопасность

1. **Смените Дефолтные Пароли**
   ```bash
   # Grafana admin password
   GF_SECURITY_ADMIN_PASSWORD=your-strong-password
   ```

2. **Ограничьте Доступ**
   - Используйте firewall rules
   - Настройте authentication в Prometheus
   - Используйте HTTPS для всех интерфейсов

3. **Регулярные Бэкапы**
   ```bash
   # Бэкап Grafana dashboards
   docker compose exec grafana grafana-cli admin backup
   
   # Бэкап Prometheus data
   docker compose exec prometheus promtool tsdb snapshot /prometheus
   ```

### Алертинг

1. **Не Спамьте**
   - Используйте группировку алертов
   - Настройте throttling для повторных уведомлений
   - Используйте severity levels

2. **Тестируйте Алерты**
   - Регулярно проверяйте notification channels
   - Используйте mock alerts для тестирования

3. **Документируйте**
   - Добавляйте описания к алертам
   - Включайте ссылки на runbooks
   - Указывайте кому эскалировать

---

## 📚 Полезные Ресурсы

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [VK Cloud Monitoring](https://cloud.vk.com/docs/ru/monitoring)
- [Node Exporter Metrics](https://github.com/prometheus/node_exporter)
- [FastAPI Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)

---

## 🆘 Поддержка

Если возникли проблемы:

1. Проверьте логи: `docker compose logs -f prometheus grafana`
2. Проверьте конфигурации в `monitoring/`
3. Откройте issue на GitHub
4. Проверьте документацию выше

---

**Version**: 1.9  
**Last Updated**: 2025-10-19  
**Status**: Production Ready

