# 📊 cAdvisor - Руководство по мониторингу Docker контейнеров

## 🔍 Что такое cAdvisor?

**cAdvisor** (Container Advisor) - это инструмент от Google для мониторинга Docker контейнеров в реальном времени.

### Основная информация:
- **Разработчик:** Google
- **Назначение:** Анализ использования ресурсов контейнерами
- **Лицензия:** Apache 2.0 (Open Source)
- **Официальный сайт:** https://github.com/google/cadvisor

---

## 💡 Для чего используется?

cAdvisor собирает, обрабатывает и предоставляет метрики о:

### 📈 Ресурсы:
- **CPU** - использование процессора каждым контейнером
- **Memory** - потребление оперативной памяти
- **Network** - сетевой трафик (входящий/исходящий)
- **Disk I/O** - операции чтения/записи на диск
- **Filesystem** - использование дискового пространства

### 🎯 Процессы:
- Количество запущенных процессов в контейнере
- Состояние контейнеров (running, stopped, etc.)
- История перезапусков

---

## 🏗️ Как работает в вашей системе?

### Архитектура:

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Host                          │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Backend  │  │ Frontend │  │   Redis  │  ...        │
│  │Container │  │Container │  │Container │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │             │                    │
│       └─────────────┴─────────────┘                    │
│                     │                                  │
│         ┌───────────▼──────────────┐                   │
│         │      cAdvisor :8080      │ ← собирает метрики│
│         └───────────┬──────────────┘                   │
│                     │                                  │
│         ┌───────────▼──────────────┐                   │
│         │   Prometheus :9090       │ ← хранит метрики  │
│         └───────────┬──────────────┘                   │
│                     │                                  │
│         ┌───────────▼──────────────┐                   │
│         │     Grafana :3001        │ ← визуализация   │
│         └──────────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

### Конфигурация (docker-compose.monitoring.yml):

```yaml
cadvisor:
  image: gcr.io/cadvisor/cadvisor:latest
  container_name: bizcard-cadvisor
  restart: unless-stopped
  privileged: true  # ← нужен доступ к системе
  ports:
    - "8080:8080"
  volumes:
    - /:/rootfs:ro           # ← чтение корневой ФС
    - /var/run:/var/run:ro   # ← Docker socket
    - /sys:/sys:ro           # ← системная информация
    - /var/lib/docker/:/var/lib/docker:ro  # ← Docker данные
  command:
    - '--housekeeping_interval=10s'  # ← каждые 10 сек
    - '--docker_only=true'           # ← только Docker
```

---

## 🚀 Как использовать?

### 1. Веб-интерфейс cAdvisor

**URL:** http://ibbase.ru:8080

**Что можно посмотреть:**
- 📊 Дашборд со всеми контейнерами
- 📈 Графики использования ресурсов в реальном времени
- 📋 Детальная информация о каждом контейнере
- 🔄 История за последние 60 секунд

**Пример просмотра:**
```
http://ibbase.ru:8080
├── / (корень) - список всех контейнеров
├── /docker/ - только Docker контейнеры
│   ├── /docker/<container-id> - детали контейнера
│   └── /docker/<container-name>
└── /metrics - метрики для Prometheus
```

### 2. REST API

**Базовый URL:** http://localhost:8080/api/v1.3/

**Основные endpoints:**

```bash
# Список всех Docker контейнеров
curl http://localhost:8080/api/v1.3/docker/

# Информация о конкретном контейнере
curl http://localhost:8080/api/v1.3/docker/<container-name>

# Пример: метрики backend контейнера
curl http://localhost:8080/api/v1.3/docker/bizcard-backend

# Метрики системы
curl http://localhost:8080/api/v1.3/machine
```

**Формат ответа (JSON):**
```json
{
  "id": "container-id",
  "name": "bizcard-backend",
  "aliases": ["backend"],
  "spec": {
    "cpu": { "limit": 2597, "mask": "0-1" },
    "memory": { "limit": 8589934592 }
  },
  "stats": [
    {
      "timestamp": "2025-10-25T10:00:00Z",
      "cpu": {
        "usage": {
          "total": 1234567890,
          "per_cpu_usage": [500000000, 734567890]
        }
      },
      "memory": {
        "usage": 536870912,
        "working_set": 536870912
      },
      "network": {
        "rx_bytes": 123456789,
        "tx_bytes": 987654321
      }
    }
  ]
}
```

### 3. Интеграция с Prometheus

cAdvisor автоматически экспортирует метрики для Prometheus:

**URL метрик:** http://localhost:8080/metrics

**Prometheus конфигурация** (уже настроена):
```yaml
scrape_configs:
  - job_name: 'cadvisor'
    scrape_interval: 15s
    static_configs:
      - targets: ['cadvisor:8080']
```

**Доступные метрики в Prometheus:**
- `container_cpu_usage_seconds_total`
- `container_memory_usage_bytes`
- `container_network_receive_bytes_total`
- `container_network_transmit_bytes_total`
- `container_fs_usage_bytes`

### 4. Визуализация в Grafana

**URL:** https://monitoring.ibbase.ru

**Готовые дашборды для импорта:**
- **ID: 893** - Docker monitoring via cAdvisor
- **ID: 14282** - Docker Container & Host Metrics

**Как импортировать:**
1. Откройте Grafana → Dashboards → Import
2. Введите ID дашборда (например, 893)
3. Выберите Prometheus как data source
4. Нажмите Import

---

## 📊 Практические примеры

### Пример 1: Мониторинг CPU всех контейнеров

**Prometheus Query:**
```promql
# Процент использования CPU по контейнерам
sum(rate(container_cpu_usage_seconds_total[1m])) by (name) * 100
```

**Результат:**
```
bizcard-backend:  45%
bizcard-frontend: 12%
bizcard-db:       8%
bizcard-redis:    3%
```

### Пример 2: Топ-5 контейнеров по памяти

**Prometheus Query:**
```promql
# Топ 5 контейнеров по использованию памяти
topk(5, container_memory_usage_bytes{name!=""})
```

### Пример 3: Сетевой трафик

**Prometheus Query:**
```promql
# Входящий трафик (MB/s)
sum(rate(container_network_receive_bytes_total[5m])) by (name) / 1024 / 1024

# Исходящий трафик (MB/s)
sum(rate(container_network_transmit_bytes_total[5m])) by (name) / 1024 / 1024
```

### Пример 4: Alert на высокое использование памяти

**Prometheus Alert:**
```yaml
- alert: ContainerHighMemory
  expr: |
    container_memory_usage_bytes{name!=""} 
    / 
    container_spec_memory_limit_bytes > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Container {{ $labels.name }} high memory usage"
    description: "{{ $labels.name }} is using {{ $value }}% of memory limit"
```

---

## 🔧 Команды для управления

### Запуск cAdvisor:
```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
docker compose -f docker-compose.monitoring.yml up -d cadvisor
```

### Остановка:
```bash
docker compose -f docker-compose.monitoring.yml stop cadvisor
```

### Перезапуск:
```bash
docker compose -f docker-compose.monitoring.yml restart cadvisor
```

### Просмотр логов:
```bash
docker logs bizcard-cadvisor -f
```

### Проверка статуса:
```bash
docker ps | grep cadvisor
curl -s http://localhost:8080/healthz
```

---

## 📈 Что мониторить в первую очередь?

### 1. **CPU Usage** (загрузка процессора)
- **Нормально:** < 70%
- **Внимание:** 70-90%
- **Критично:** > 90%

**Что делать если высокая:**
- Оптимизировать код
- Добавить кеширование
- Масштабировать горизонтально (больше контейнеров)

### 2. **Memory Usage** (память)
- **Нормально:** < 80% от лимита
- **Внимание:** 80-95%
- **Критично:** > 95%

**Что делать если высокая:**
- Найти утечки памяти
- Увеличить лимиты
- Оптимизировать запросы к БД

### 3. **Network I/O** (сеть)
- **Нормально:** стабильный трафик
- **Внимание:** резкие скачки
- **Критично:** постоянные 100 Мбит/с+

**Что делать:**
- Проверить атаки (DDoS)
- Оптимизировать API запросы
- Использовать CDN для статики

### 4. **Disk I/O** (диск)
- **Нормально:** < 80% IOPS
- **Внимание:** постоянная запись/чтение
- **Критично:** очередь операций > 10

**Что делать:**
- Оптимизировать SQL запросы
- Добавить индексы в БД
- Использовать SSD вместо HDD

---

## 🎯 Best Practices

### ✅ Рекомендации:

1. **Регулярный мониторинг**
   - Проверяйте дашборды минимум раз в день
   - Настройте алерты на критичные метрики

2. **Историческая аналитика**
   - Prometheus хранит данные 15 дней
   - Экспортируйте в long-term storage если нужно больше

3. **Capacity Planning**
   - Анализируйте тренды использования ресурсов
   - Планируйте масштабирование заранее

4. **Оптимизация**
   - Используйте метрики для поиска узких мест
   - Применяйте изменения постепенно
   - Измеряйте результаты

5. **Алерты**
   - Не создавайте слишком много алертов (alert fatigue)
   - Группируйте похожие проблемы
   - Добавляйте инструкции по устранению

---

## 🔗 Полезные ссылки

- **Официальная документация:** https://github.com/google/cadvisor/blob/master/docs/
- **API Reference:** https://github.com/google/cadvisor/blob/master/docs/api.md
- **Prometheus Integration:** https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md
- **Grafana Dashboards:** https://grafana.com/grafana/dashboards/?search=cadvisor

---

## 🆘 Troubleshooting

### Проблема: cAdvisor не видит контейнеры

**Решение:**
```bash
# Проверить что Docker socket доступен
ls -la /var/run/docker.sock

# Перезапустить cAdvisor с правами
docker compose -f docker-compose.monitoring.yml restart cadvisor
```

### Проблема: Высокая нагрузка от cAdvisor

**Решение:**
```bash
# Увеличить интервал опроса (в docker-compose.monitoring.yml)
command:
  - '--housekeeping_interval=30s'  # вместо 10s
```

### Проблема: Не работает UI

**Решение:**
```bash
# Проверить порт
netstat -tulpn | grep 8080

# Проверить логи
docker logs bizcard-cadvisor --tail 50
```

---

## ✅ Checklist быстрой проверки

```
☐ cAdvisor запущен (docker ps | grep cadvisor)
☐ UI доступен (http://localhost:8080)
☐ Метрики собираются (http://localhost:8080/metrics)
☐ Prometheus собирает данные (проверить targets)
☐ Grafana показывает графики
☐ Алерты настроены
```

---

**Создано:** 2025-10-25  
**Версия:** 1.0  
**Автор:** FastAPI Business Card CRM Team
