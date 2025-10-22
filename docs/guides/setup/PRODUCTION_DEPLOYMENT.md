# 🚀 Руководство по Production Deployment - ibbase v2.4

**Дата:** 2025-10-20  
**Версия:** v2.4  
**Домен:** ibbase.ru  
**Статус:** ✅ РАЗВЕРНУТО И РАБОТАЕТ

---

## 📋 Обзор

Этот документ описывает production deployment системы ibbase v2.4 на домене **ibbase.ru** с полным SSL/TLS шифрованием, мониторингом и высокой доступностью.

---

## 🌐 Production URL-адреса

| Сервис | URL | Статус |
|--------|-----|--------|
| **Frontend (Основное приложение)** | https://ibbase.ru | ✅ Активен |
| **API Backend** | https://api.ibbase.ru | ✅ Активен |
| **API Документация** | https://api.ibbase.ru/docs | ✅ Активен |
| **Мониторинг (Grafana)** | https://monitoring.ibbase.ru | ✅ Активен |
| **Prometheus** | http://localhost:9090 | ✅ Внутренний |

---

## 🔒 Конфигурация SSL/TLS

### Детали сертификата
- **Провайдер:** Let's Encrypt
- **Тип:** ECDSA
- **Покрытые домены:**
  - ibbase.ru
  - www.ibbase.ru
  - api.ibbase.ru
  - monitoring.ibbase.ru
- **Срок действия:** до 2026-01-17 (действителен 89 дней)
- **Автообновление:** ✅ Включено через certbot

### Расположение сертификатов
```bash
/etc/letsencrypt/live/ibbase.ru/fullchain.pem
/etc/letsencrypt/live/ibbase.ru/privkey.pem
```

### Команды обновления
```bash
sudo certbot renew --dry-run  # Тестовое обновление
sudo certbot renew            # Реальное обновление
```

---

## 🐳 Docker Сервисы

### Активные контейнеры

| Контейнер | Статус | Порты | Назначение |
|-----------|--------|-------|------------|
| **bizcard-frontend** | Работает | 3000:80, 8443:443 | React UI |
| **bizcard-backend** | Работает | 8000:8000 | FastAPI |
| **bizcard-db** | Работает | 5432:5432 | PostgreSQL |
| **bizcard-redis** | Работает | 6379:6379 | Redis кэш |
| **bizcard-celery-worker** | Работает | - | Очередь задач |
| **bizcard-grafana** | Работает | 3001:3000 | Мониторинг |
| **bizcard-prometheus** | Работает | 9090:9090 | Метрики |
| **bizcard-node-exporter** | Работает | 9100:9100 | Системные метрики |
| **bizcard-cadvisor** | Работает | 8080:8080 | Метрики контейнеров |
| **bizcard-postgres-exporter** | Работает | 9187:9187 | Метрики БД |

### Управление сервисами

```bash
# Просмотр всех сервисов
docker compose ps

# Перезапуск конкретного сервиса
docker compose restart backend

# Просмотр логов
docker compose logs -f backend

# Полная пересборка и перезапуск
docker compose up -d --build
```

---

## 🌍 Конфигурация Nginx

### Файлы конфигурации

| Файл | Назначение |
|------|------------|
| `/etc/nginx/sites-available/ibbase.ru` | Прокси для frontend |
| `/etc/nginx/sites-available/api.ibbase.ru` | Прокси для API backend |
| `/etc/nginx/sites-available/monitoring.ibbase.ru` | Прокси для Grafana |

### Основная конфигурация Frontend (`ibbase.ru`)
```nginx
# Основной домен - Frontend (React)
server {
    server_name ibbase.ru www.ibbase.ru;
    
    client_max_body_size 20M;
    
    # Для Let's Encrypt ACME challenge
    location ^~ /.well-known/acme-challenge/ {
        default_type "text/plain";
        root /var/www/html;
    }
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/ibbase.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ibbase.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

# HTTP редирект на HTTPS
server {
    if ($host = ibbase.ru) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    server_name ibbase.ru www.ibbase.ru;
    return 404;
}
```

### Управление Nginx
```bash
# Тест конфигурации
sudo nginx -t

# Перезагрузка конфигурации
sudo nginx -s reload

# Перезапуск Nginx
sudo systemctl restart nginx

# Просмотр логов
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

---

## 🔥 Конфигурация Firewall

### Статус UFW
```
Статус: активен

Кому                       Действие    Откуда
----                       --------    ------
80/tcp                     РАЗРЕШИТЬ   Anywhere       # HTTP
443/tcp                    РАЗРЕШИТЬ   Anywhere       # HTTPS
22/tcp                     РАЗРЕШИТЬ   Anywhere       # SSH
3000/tcp                   РАЗРЕШИТЬ   Anywhere       # Frontend (Docker)
8443/tcp                   РАЗРЕШИТЬ   Anywhere       # Frontend HTTPS
```

### Управление Firewall
```bash
# Проверка статуса
sudo ufw status verbose

# Разрешить новый порт
sudo ufw allow 9090/tcp comment 'Prometheus'

# Запретить порт
sudo ufw deny 5432/tcp

# Перезагрузка
sudo ufw reload
```

---

## 📊 Настройка мониторинга

### Grafana
- **URL:** https://monitoring.ibbase.ru
- **Credentials по умолчанию:** admin / admin (СМЕНИТЬ ПРИ ПЕРВОМ ВХОДЕ!)
- **Дашборды:**
  - Системные метрики
  - Метрики приложения
  - Метрики базы данных
  - Задачи Celery

### Prometheus
- **URL:** http://localhost:9090
- **Интервал сбора:** 15 секунд
- **Хранение:** 15 дней
- **Цели мониторинга:**
  - Метрики FastAPI приложения
  - Node exporter (система)
  - cAdvisor (контейнеры)
  - PostgreSQL exporter

### Эндпоинты метрик
```bash
# Метрики приложения
curl https://api.ibbase.ru/metrics

# Цели Prometheus
curl http://localhost:9090/api/v1/targets

# Здоровье Grafana
curl https://monitoring.ibbase.ru/api/health
```

---

## 🗄️ Управление базой данных

### Параметры подключения
- **Хост:** localhost (через Docker: bizcard-db)
- **Порт:** 5432
- **База данных:** bizcard_crm
- **Пользователь:** postgres
- **Пароль:** (хранится в docker-compose.yml)

### Операции с базой данных

```bash
# Подключение к базе данных
docker exec -it bizcard-db psql -U postgres -d bizcard_crm

# Резервное копирование базы данных
docker exec bizcard-db pg_dump -U postgres bizcard_crm > backup_$(date +%Y%m%d).sql

# Восстановление базы данных
docker exec -i bizcard-db psql -U postgres bizcard_crm < backup.sql

# Просмотр размера базы данных
docker exec bizcard-db psql -U postgres -d bizcard_crm -c "SELECT pg_size_pretty(pg_database_size('bizcard_crm'));"
```

### Автоматические резервные копии
- **Расписание:** Ежедневно в 2:00 UTC
- **Расположение:** `/home/ubuntu/fastapi-bizcard-crm-ready/backups/`
- **Хранение:** 7 дней
- **Скрипт:** `/home/ubuntu/fastapi-bizcard-crm-ready/scripts/backup-db.sh`

---

## 🔄 Процесс развертывания

### Стандартное развертывание

```bash
# 1. Получить последние изменения
cd /home/ubuntu/fastapi-bizcard-crm-ready
git pull origin main

# 2. Пересобрать и перезапустить сервисы
docker compose down
docker compose up -d --build

# 3. Проверить сервисы
docker compose ps

# 4. Запустить smoke tests
./smoke_test_prod.sh

# 5. Проверить логи на ошибки
docker compose logs -f --tail=100
```

### Развертывание без простоя (Zero-Downtime)

```bash
# 1. Получить изменения
git pull origin main

# 2. Собрать новые образы
docker compose build

# 3. Последовательный перезапуск
docker compose up -d --no-deps --build backend
sleep 10
docker compose up -d --no-deps --build frontend
sleep 5
docker compose up -d --no-deps --build celery-worker

# 4. Проверка
./smoke_test_prod.sh
```

---

## 🧪 Smoke Tests

### Запуск production тестов
```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
./smoke_test_prod.sh
```

### Покрытие тестами
✅ HTTPS доступ к Frontend  
✅ HTTP редирект на HTTPS  
✅ WWW редирект  
✅ Проверка здоровья API  
✅ Версия API  
✅ Документация API  
✅ Метрики API  
✅ Доступ к Grafana  
✅ Валидность SSL сертификата  
✅ Статус Docker сервисов  
✅ Подключение к PostgreSQL  
✅ Подключение к Redis  

**Успешность:** 93% (15/16 тестов)

---

## 🚨 Устранение неполадок

### Сервис не запускается

```bash
# Проверка логов
docker compose logs service_name

# Перезапуск сервиса
docker compose restart service_name

# Полная пересборка
docker compose down
docker compose up -d --build
```

### Проблемы с SSL сертификатом

```bash
# Тест обновления
sudo certbot renew --dry-run

# Принудительное обновление
sudo certbot renew --force-renewal

# Проверка срока действия
sudo certbot certificates
```

### Проблемы с конфигурацией Nginx

```bash
# Тест конфигурации
sudo nginx -t

# Просмотр лога ошибок
sudo tail -f /var/log/nginx/error.log

# Перезапуск Nginx
sudo systemctl restart nginx
```

### Проблемы с подключением к БД

```bash
# Проверка работы базы данных
docker exec bizcard-db pg_isready

# Просмотр логов базы данных
docker logs bizcard-db

# Перезапуск базы данных
docker compose restart db
```

---

## 📈 Оптимизация производительности

### Текущая конфигурация
- **Workers:** 2 Celery worker'а
- **Concurrency:** 2 на worker
- **Database connections:** Pool size 10
- **Redis max memory:** 256MB
- **Nginx worker processes:** 2

### Рекомендации по масштабированию
1. Увеличить количество Celery workers для пакетной обработки
2. Добавить read replicas для PostgreSQL
3. Реализовать Redis cluster для высокой доступности
4. Добавить CDN для статических ресурсов
5. Включить HTTP/2 в Nginx

---

## 🔐 Чек-лист безопасности

- [x] SSL/TLS включен для всех публичных эндпоинтов
- [x] Firewall (UFW) настроен
- [x] База данных не доступна публично
- [x] Пароли администратора изменены с дефолтных
- [x] Rate limiting включен на API
- [x] CORS настроен правильно
- [x] Автоматические обновления безопасности включены
- [x] Стратегия резервного копирования реализована
- [x] Мониторинг и alerting настроены
- [ ] TODO: Настроить fail2ban для защиты SSH
- [ ] TODO: Включить WAF на уровне приложения

---

## 📞 Поддержка и контакты

**Production сервер:**
- IP: 95.163.183.25
- SSH: ubuntu@95.163.183.25
- Локация: VK Cloud

**Ключевые контакты:**
- Системный администратор: [Ваше имя]
- Разработчик: [Ваше имя]

**Документация:**
- GitHub: https://github.com/newwdead/CRM
- Release Notes: `RELEASE_NOTES_v2.4.md`
- Руководства по настройке: `TELEGRAM_SETUP.md`, `WHATSAPP_SETUP.md`, `SSL_SETUP.md`

---

## 📝 Журнал изменений

### 2025-10-20 - Production Deployment v2.4
- ✅ Развернут ibbase v2.4 на production
- ✅ Настроены SSL сертификаты (Let's Encrypt)
- ✅ Настроен Nginx reverse proxy
- ✅ Все сервисы работают
- ✅ Активен мониторинг стек (Grafana + Prometheus)
- ✅ Работает очередь Celery + Redis
- ✅ Настроен Firewall
- ✅ Пройдены smoke tests (93%)

---

## 🔍 Полезные команды

### Мониторинг системы
```bash
# Проверка использования ресурсов
docker stats

# Проверка дискового пространства
df -h

# Проверка памяти
free -h

# Проверка CPU
top

# Проверка сетевых подключений
sudo ss -tlnp | grep -E ":(80|443|8000|3000)"
```

### Работа с логами
```bash
# Все логи контейнеров
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f backend

# Последние 100 строк
docker compose logs --tail=100

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Системные логи
sudo journalctl -u nginx -f
sudo journalctl -u docker -f
```

### Управление Docker
```bash
# Остановка всех сервисов
docker compose down

# Запуск всех сервисов
docker compose up -d

# Перезапуск одного сервиса
docker compose restart backend

# Просмотр использования ресурсов
docker compose top

# Очистка неиспользуемых ресурсов
docker system prune -a

# Просмотр логов конкретного контейнера
docker logs bizcard-backend -f --tail=100
```

### Работа с Git
```bash
# Проверка текущей версии
git log --oneline -5

# Просмотр изменений
git status

# Обновление из репозитория
git pull origin main

# Просмотр тегов
git tag -l
```

---

## 📊 Мониторинг метрик

### Ключевые метрики для отслеживания

**Системные метрики:**
- CPU использование < 70%
- RAM использование < 80%
- Disk использование < 85%
- Network latency < 100ms

**Метрики приложения:**
- Response time API < 500ms
- Request rate: мониторинг
- Error rate < 1%
- Success rate > 99%

**Метрики базы данных:**
- Активные подключения < 80
- Query execution time < 1s
- Размер БД: мониторинг роста
- Deadlocks: 0

**Метрики Celery:**
- Queue length < 100
- Task success rate > 95%
- Average processing time < 5s
- Failed tasks: мониторинг

### Alerting правила

Настроить оповещения в Grafana для:
- CPU > 80% в течение 5 минут
- Memory > 90% в течение 5 минут
- Disk > 90%
- API error rate > 5%
- Database connections > 90
- SSL сертификат expires < 30 дней

---

## 🔄 Процедуры резервного копирования

### Автоматическое резервное копирование

**База данных:**
```bash
# Расположение скрипта
/home/ubuntu/fastapi-bizcard-crm-ready/scripts/backup-db.sh

# Cron задание (ежедневно в 2:00)
0 2 * * * /home/ubuntu/fastapi-bizcard-crm-ready/scripts/backup-db.sh

# Проверка последних бэкапов
ls -lh /home/ubuntu/fastapi-bizcard-crm-ready/backups/
```

**Файлы (uploads):**
```bash
# Бэкап директории uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz /home/ubuntu/fastapi-bizcard-crm-ready/uploads/

# Копирование на удаленный сервер
scp uploads_backup_*.tar.gz user@backup-server:/backups/
```

### Восстановление из резервной копии

```bash
# 1. Остановить приложение
docker compose down

# 2. Восстановить базу данных
docker compose up -d db
sleep 5
docker exec -i bizcard-db psql -U postgres bizcard_crm < backups/backup_YYYYMMDD.sql

# 3. Восстановить файлы
tar -xzf uploads_backup_YYYYMMDD.tar.gz -C /home/ubuntu/fastapi-bizcard-crm-ready/

# 4. Запустить приложение
docker compose up -d

# 5. Проверить работоспособность
./smoke_test_prod.sh
```

---

## 🆘 Аварийные процедуры

### Полный отказ сервиса

```bash
# 1. Проверка статуса всех сервисов
docker compose ps
sudo systemctl status nginx

# 2. Просмотр критических логов
docker compose logs --tail=100
sudo tail -100 /var/log/nginx/error.log

# 3. Перезапуск всех сервисов
docker compose down
docker compose up -d --build

# 4. Проверка доступности
./smoke_test_prod.sh
```

### Откат на предыдущую версию

```bash
# 1. Просмотр доступных версий
git tag -l

# 2. Переключение на предыдущую версию
git checkout v2.3

# 3. Развертывание предыдущей версии
docker compose down
docker compose up -d --build

# 4. Проверка
./smoke_test_prod.sh

# 5. Возврат к текущей версии (если нужно)
git checkout main
```

### Проблемы с производительностью

```bash
# 1. Проверка нагрузки
docker stats
htop

# 2. Анализ медленных запросов в БД
docker exec bizcard-db psql -U postgres -d bizcard_crm -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# 3. Очистка кэша Redis
docker exec bizcard-redis redis-cli FLUSHALL

# 4. Перезапуск проблемных сервисов
docker compose restart backend celery-worker
```

---

## 📚 Дополнительные ресурсы

### Документация
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

### Внутренняя документация проекта
- `README.md` - Общее описание проекта
- `RELEASE_NOTES_v2.4.md` - Примечания к релизу
- `TELEGRAM_SETUP.md` - Настройка Telegram интеграции
- `WHATSAPP_SETUP.md` - Настройка WhatsApp интеграции
- `SSL_SETUP.md` - Настройка SSL сертификатов
- `CELERY_FIX_LOG.md` - Лог исправлений Celery
- `TEST_RESULTS_MANUAL_v2.4.md` - Результаты тестирования

---

**Версия документа:** 1.0  
**Последнее обновление:** 2025-10-20 18:30 UTC  
**Статус:** Production Ready ✅  
**Язык:** Русский 🇷🇺
