# Production Deployment Guide - BizCard CRM

## 📋 Содержание

1. [Подготовка сервера](#подготовка-сервера)
2. [Настройка домена и SSL](#настройка-домена-и-ssl)
3. [Production конфигурация](#production-конфигурация)
4. [Backup и восстановление](#backup-и-восстановление)
5. [Мониторинг](#мониторинг)
6. [Обслуживание](#обслуживание)
7. [Безопасность](#безопасность)

---

## 🚀 Подготовка сервера

### Системные требования

- **OS**: Ubuntu 22.04 LTS или новее
- **RAM**: Минимум 2GB, рекомендуется 4GB
- **CPU**: 2+ cores
- **Disk**: 20GB+ свободного места
- **Docker**: 24.0+
- **Docker Compose**: 2.20+

### Установка зависимостей

```bash
# Обновление системы
sudo apt-get update && sudo apt-get upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo apt-get install docker-compose-plugin -y

# Установка Nginx
sudo apt-get install nginx -y

# Установка Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Настройка firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

---

## 🌐 Настройка домена и SSL

### 1. Настройка DNS записей

В панели управления доменом добавьте A-записи:

| Запись | Тип | Значение | TTL |
|--------|-----|----------|-----|
| @ | A | YOUR_SERVER_IP | 3600 |
| www | A | YOUR_SERVER_IP | 3600 |
| api | A | YOUR_SERVER_IP | 3600 |
| monitoring | A | YOUR_SERVER_IP | 3600 |

### 2. Проверка DNS

```bash
# Проверьте, что DNS настроен
for domain in yourdomain.com www.yourdomain.com api.yourdomain.com monitoring.yourdomain.com; do
    echo -n "$domain: "
    host $domain 2>&1 | grep "has address" || echo "НЕ НАСТРОЕН"
done
```

### 3. Получение SSL сертификатов

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
./get_ssl_certificates.sh
```

Скрипт автоматически:
- Проверит DNS записи
- Получит SSL сертификаты от Let's Encrypt
- Настроит Nginx для HTTPS
- Настроит автообновление сертификатов

---

## ⚙️ Production конфигурация

### 1. Создание файла переменных окружения

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
cp .env.production.example .env.production
```

Отредактируйте `.env.production`:

```bash
# Сгенерируйте безопасные пароли
openssl rand -hex 32  # Для JWT_SECRET_KEY
openssl rand -base64 16  # Для DB_PASSWORD

nano .env.production
```

**Важные параметры:**
- `DB_PASSWORD` - пароль базы данных
- `JWT_SECRET_KEY` - секретный ключ для JWT
- `GRAFANA_ADMIN_PASSWORD` - пароль Grafana

### 2. Обновление Nginx конфигураций

После получения SSL, обновите конфигурации в `/etc/nginx/sites-available/` и замените домены:

```bash
# Замените YOUR_DOMAIN на ваш домен в конфигурациях
sudo sed -i 's/ibbase.ru/yourdomain.com/g' /etc/nginx/sites-available/*
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Обновление CORS в backend

Отредактируйте `backend/app/main.py` и замените домены в `allow_origins`:

```python
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://api.yourdomain.com",
    # ...
]
```

### 4. Обновление Grafana URL

Отредактируйте `docker-compose.prod.yml`:

```yaml
- GF_SERVER_ROOT_URL=https://monitoring.yourdomain.com
- GF_SERVER_DOMAIN=monitoring.yourdomain.com
```

### 5. Запуск в production режиме

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Остановите dev версию
docker compose down

# Запустите production версию
docker compose --env-file .env.production \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f docker-compose.monitoring.yml \
  up -d

# Проверьте статус
docker ps
```

---

## 💾 Backup и восстановление

### Автоматический backup

Backup базы данных настроен автоматически (cron):
- **Расписание**: Ежедневно в 3:00 AM
- **Хранение**: 30 дней
- **Локация**: `./backups/`

**Просмотр логов backup:**
```bash
tail -f /var/log/bizcard_backup.log
```

### Ручной backup

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
./scripts/backup_database.sh
```

### Восстановление из backup

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Список доступных backup
./scripts/restore_database.sh

# Восстановление конкретного backup
./scripts/restore_database.sh backup_bizcard_crm_20251019_210505.sql.gz
```

**⚠️ ВНИМАНИЕ:** Перед восстановлением создается safety backup!

---

## 📊 Мониторинг

### Доступ к Grafana

URL: `https://monitoring.yourdomain.com`

**Логин по умолчанию:**
- Username: `admin`
- Password: `admin` (измените в `.env.production`)

### Доступные дашборды

1. **System Overview** - CPU, RAM, Disk, Network
2. **Application Metrics** - API requests, OCR processing, errors

### Prometheus

Prometheus доступен только локально:
- URL: `http://localhost:9090` (SSH tunnel)
- Метрики: `http://localhost:9090/metrics`

### Health Check

Проверка статуса всех сервисов:

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
./scripts/health_check.sh
```

---

## 🛠️ Обслуживание

### Просмотр логов

```bash
# Backend logs
docker logs bizcard-backend -f --tail 100

# Frontend/Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Database logs
docker logs bizcard-db -f --tail 100

# Grafana logs
docker logs bizcard-grafana -f --tail 100
```

### Перезапуск сервисов

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Перезапуск всех сервисов
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Перезапуск конкретного сервиса
docker restart bizcard-backend
```

### Обновление приложения

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Получить последние изменения
git pull

# Пересобрать и перезапустить
docker compose --env-file .env.production \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f docker-compose.monitoring.yml \
  up -d --build
```

### Очистка Docker

```bash
# Удалить неиспользуемые образы
docker image prune -a

# Очистить систему
docker system prune -a --volumes
```

---

## 🔒 Безопасность

### 1. Изменить пароли по умолчанию

```bash
# Смените пароль Grafana admin
# через Web UI: Profile → Change Password

# Смените пароль admin в приложении
# через Web UI: Admin Panel → Users
```

### 2. Настроить SSH ключи

```bash
# Отключить парольную аутентификацию SSH
sudo nano /etc/ssh/sshd_config

# Установите:
PasswordAuthentication no
PubkeyAuthentication yes

sudo systemctl restart sshd
```

### 3. Включить fail2ban

```bash
sudo apt-get install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 4. Обновления безопасности

```bash
# Автоматические обновления безопасности
sudo apt-get install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 5. Регулярные проверки

```bash
# Health check
./scripts/health_check.sh

# Проверка SSL сертификатов
sudo certbot certificates

# Проверка открытых портов
sudo netstat -tulpn
```

---

## 📞 Поддержка и устранение неполадок

### Backend не запускается

```bash
# Проверьте логи
docker logs bizcard-backend

# Проверьте переменные окружения
docker exec bizcard-backend env

# Проверьте подключение к БД
docker exec bizcard-backend curl -f http://localhost:8000/version
```

### Frontend возвращает 502

```bash
# Проверьте статус backend
docker ps | grep bizcard-backend

# Проверьте конфигурацию Nginx
sudo nginx -t

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/error.log
```

### Database проблемы

```bash
# Проверьте статус БД
docker exec bizcard-db pg_isready -U postgres

# Проверьте размер БД
docker exec bizcard-db psql -U postgres -d bizcard_crm -c "SELECT pg_size_pretty(pg_database_size('bizcard_crm'));"

# Восстановите из backup если нужно
./scripts/restore_database.sh
```

### SSL сертификаты истекли

```bash
# Проверьте статус
sudo certbot certificates

# Обновите сертификаты вручную
sudo certbot renew --force-renewal

# Перезапустите Nginx
sudo systemctl reload nginx
```

---

## 🎯 Checklist перед production запуском

- [ ] DNS записи настроены и работают
- [ ] SSL сертификаты получены
- [ ] `.env.production` настроен (пароли изменены)
- [ ] CORS обновлен с правильными доменами
- [ ] Grafana URL обновлен
- [ ] Firewall настроен (UFW)
- [ ] Автоматический backup настроен
- [ ] Health checks работают
- [ ] Логи ротируются
- [ ] Пароли по умолчанию изменены
- [ ] SSH ключи настроены
- [ ] Мониторинг Grafana работает
- [ ] Все тесты пройдены

---

## 📚 Дополнительная документация

- [README.md](README.md) - Основная документация
- [README.ru.md](README.ru.md) - Русская версия
- [DOMAIN_SSL_SETUP.md](DOMAIN_SSL_SETUP.md) - Детальная настройка SSL
- [MONITORING_SETUP.md](MONITORING_SETUP.md) - Настройка мониторинга
- [AUTH_SETUP.md](AUTH_SETUP.md) - Аутентификация
- [RELEASE_NOTES_v2.2.md](RELEASE_NOTES_v2.2.md) - Последний релиз

---

**Версия документа**: 1.0  
**Последнее обновление**: 2025-10-19  
**BizCard CRM v2.2**

