# 🌐 Domain & SSL Setup для VK Cloud

## Overview

Пошаговая инструкция по настройке домена и SSL сертификата для BizCard CRM в VK Cloud.

---

## 📋 План Действий

1. ✅ Получить доменное имя
2. ✅ Настроить DNS записи
3. ✅ Настроить Nginx как reverse proxy
4. ✅ Получить SSL сертификат (Let's Encrypt)
5. ✅ Настроить автообновление сертификата
6. ✅ Проверить безопасность

---

## 🌐 Шаг 1: Получение Домена

### Варианты:

**Вариант A: Купить домен**
- [Reg.ru](https://www.reg.ru/) - от 99₽/год (.ru)
- [Timeweb](https://timeweb.com/) - от 199₽/год
- [Namecheap](https://www.namecheap.com/) - от $8.88/год (.com)

**Вариант B: Бесплатный поддомен**
- [Freenom](https://www.freenom.com/) - бесплатные домены (.tk, .ml, .ga)
- [DuckDNS](https://www.duckdns.org/) - бесплатные поддомены
- [No-IP](https://www.noip.com/) - бесплатные динамические DNS

**Рекомендация:** Купите нормальный домен для production (например, `bizcard-crm.ru`)

---

## 🔗 Шаг 2: Настройка DNS

### 2.1 Получите IP адрес VK Cloud сервера

```bash
# На VK Cloud сервере
curl ifconfig.me
# Или
ip addr show
```

**Пример вывода:** `87.250.250.123`

### 2.2 Настройте DNS записи

В панели управления доменом (например, на reg.ru) добавьте A-записи:

| Тип | Имя | Значение | TTL |
|-----|-----|----------|-----|
| A | @ | 87.250.250.123 | 3600 |
| A | www | 87.250.250.123 | 3600 |
| A | monitoring | 87.250.250.123 | 3600 |
| A | api | 87.250.250.123 | 3600 |

**Результат:**
- `bizcard-crm.ru` → Frontend
- `www.bizcard-crm.ru` → Frontend
- `monitoring.bizcard-crm.ru` → Grafana
- `api.bizcard-crm.ru` → Backend API

### 2.3 Проверка DNS

```bash
# Подождите 5-10 минут и проверьте
dig bizcard-crm.ru +short
# Должен вернуть ваш IP: 87.250.250.123

# Проверка поддоменов
dig monitoring.bizcard-crm.ru +short
dig api.bizcard-crm.ru +short
```

---

## 🔧 Шаг 3: Установка Nginx

### 3.1 Установка на VK Cloud сервере

```bash
# SSH на сервер
ssh ubuntu@87.250.250.123

# Установка Nginx
sudo apt update
sudo apt install -y nginx

# Проверка
sudo systemctl status nginx
```

### 3.2 Создание конфигурации Nginx

```bash
# Удаляем дефолтную конфигурацию
sudo rm /etc/nginx/sites-enabled/default

# Создаем конфигурацию для нашего приложения
sudo nano /etc/nginx/sites-available/bizcard-crm
```

**Содержимое файла `/etc/nginx/sites-available/bizcard-crm`:**

```nginx
# Frontend - Главный домен
server {
    listen 80;
    server_name bizcard-crm.ru www.bizcard-crm.ru;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # File uploads
    location /files/ {
        proxy_pass http://localhost:8000/files/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # For Let's Encrypt certificate verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}

# API - Отдельный поддомен
server {
    listen 80;
    server_name api.bizcard-crm.ru;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}

# Monitoring - Grafana
server {
    listen 80;
    server_name monitoring.bizcard-crm.ru;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for live dashboards
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
```

### 3.3 Активация конфигурации

```bash
# Создаем симлинк
sudo ln -s /etc/nginx/sites-available/bizcard-crm /etc/nginx/sites-enabled/

# Проверяем конфигурацию
sudo nginx -t

# Перезапускаем Nginx
sudo systemctl restart nginx
```

### 3.4 Проверка

Откройте в браузере: `http://bizcard-crm.ru`
Должен открыться ваш сайт (пока по HTTP).

---

## 🔒 Шаг 4: Установка SSL (Let's Encrypt)

### 4.1 Установка Certbot

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx
```

### 4.2 Получение SSL сертификата

**Важно:** Убедитесь что:
- DNS записи настроены и работают
- Nginx запущен и доступен по HTTP
- Порты 80 и 443 открыты в firewall

```bash
# Получаем сертификаты для всех доменов
sudo certbot --nginx \
  -d bizcard-crm.ru \
  -d www.bizcard-crm.ru \
  -d api.bizcard-crm.ru \
  -d monitoring.bizcard-crm.ru

# Следуйте инструкциям:
# 1. Введите email для уведомлений
# 2. Согласитесь с Terms of Service (Y)
# 3. Newsletter (N - необязательно)
# 4. Redirect HTTP to HTTPS? (2 - Yes, redirect)
```

**Certbot автоматически:**
- Получит сертификаты от Let's Encrypt
- Обновит конфигурацию Nginx
- Настроит редирект с HTTP на HTTPS
- Настроит автообновление сертификатов

### 4.3 Проверка SSL

```bash
# Проверка сертификата
sudo certbot certificates

# Должно показать:
# Found the following certs:
#   Certificate Name: bizcard-crm.ru
#     Domains: bizcard-crm.ru www.bizcard-crm.ru api.bizcard-crm.ru monitoring.bizcard-crm.ru
#     Expiry Date: 2026-01-17 (VALID: 89 days)
```

Откройте в браузере: `https://bizcard-crm.ru` 🔒

### 4.4 Тест автообновления

```bash
# Проверка автообновления (dry run)
sudo certbot renew --dry-run

# Должно показать: Congratulations, all renewals succeeded
```

---

## ⚙️ Шаг 5: Финальная Настройка

### 5.1 Обновление Grafana URL

Отредактируйте `docker-compose.monitoring.yml`:

```yaml
grafana:
  environment:
    - GF_SERVER_ROOT_URL=https://monitoring.bizcard-crm.ru
    - GF_SERVER_DOMAIN=monitoring.bizcard-crm.ru
```

### 5.2 Обновление CORS в Backend

Отредактируйте `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bizcard-crm.ru",
        "https://www.bizcard-crm.ru",
        "https://monitoring.bizcard-crm.ru",
        "http://localhost:3000",  # Для разработки
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 5.3 Перезапуск сервисов

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Пересобираем с новыми настройками
docker compose down
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               -f docker-compose.monitoring.yml \
               up -d --build
```

---

## 🔐 Шаг 6: Настройка Firewall (VK Cloud)

### 6.1 В веб-консоли VK Cloud

1. Перейдите в **Облачные вычисления** → **Виртуальные машины**
2. Выберите вашу VM
3. Перейдите в **Файрвол** → **Security Groups**
4. Добавьте правила:

| Направление | Порт | Протокол | Источник | Назначение |
|-------------|------|----------|----------|------------|
| Входящий | 22 | TCP | Ваш IP | SSH |
| Входящий | 80 | TCP | 0.0.0.0/0 | HTTP |
| Входящий | 443 | TCP | 0.0.0.0/0 | HTTPS |

⚠️ **Закройте все остальные порты** (3000, 3001, 8000, 9090, 9100 и т.д.)

Доступ к ним будет только через Nginx reverse proxy.

### 6.2 Проверка Firewall (на сервере)

```bash
# Установка UFW (если еще не установлен)
sudo apt install -y ufw

# Настройка правил
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Включение firewall
sudo ufw enable

# Проверка статуса
sudo ufw status verbose
```

---

## 🧪 Шаг 7: Проверка и Тестирование

### 7.1 Проверка SSL

```bash
# SSL Labs Test
# Откройте: https://www.ssllabs.com/ssltest/
# Введите: bizcard-crm.ru
# Должны получить оценку A или A+

# Или через командную строку
curl -I https://bizcard-crm.ru

# Должно вернуть:
# HTTP/2 200
# server: nginx
# strict-transport-security: max-age=31536000
```

### 7.2 Проверка всех доменов

```bash
# Frontend
curl -I https://bizcard-crm.ru
curl -I https://www.bizcard-crm.ru

# API
curl https://api.bizcard-crm.ru/version

# Monitoring
curl -I https://monitoring.bizcard-crm.ru

# Проверка редиректа HTTP → HTTPS
curl -I http://bizcard-crm.ru
# Должен вернуть: HTTP/1.1 301 Moved Permanently
# Location: https://bizcard-crm.ru/
```

### 7.3 Функциональное тестирование

1. **Frontend**: https://bizcard-crm.ru
   - Должна открыться главная страница
   - Login/Register работают
   - Upload business card работает

2. **API**: https://api.bizcard-crm.ru/docs
   - Swagger UI должен открыться
   - API endpoints доступны

3. **Monitoring**: https://monitoring.bizcard-crm.ru
   - Grafana login page
   - Dashboards работают

---

## 📊 Шаг 8: Мониторинг SSL

### 8.1 Настройка уведомлений о сроке действия

Certbot автоматически настраивает cron для обновления:

```bash
# Проверка cron задачи
sudo systemctl status certbot.timer

# Просмотр логов обновлений
sudo journalctl -u certbot -n 50
```

### 8.2 Ручное обновление (если нужно)

```bash
# Обновить все сертификаты
sudo certbot renew

# Обновить конкретный домен
sudo certbot renew --cert-name bizcard-crm.ru

# После обновления перезапустить Nginx
sudo systemctl reload nginx
```

---

## 🔧 Troubleshooting

### Проблема: DNS не резолвится

**Решение:**
```bash
# Проверка DNS
dig bizcard-crm.ru +short

# Если не работает, подождите 10-30 минут (TTL)
# Или обновите DNS кеш
sudo systemd-resolve --flush-caches
```

### Проблема: Certbot не может получить сертификат

**Ошибка:** `Failed authorization procedure`

**Решение:**
```bash
# 1. Проверьте что домен доступен по HTTP
curl http://bizcard-crm.ru

# 2. Проверьте Nginx
sudo nginx -t
sudo systemctl status nginx

# 3. Проверьте firewall
sudo ufw status
# Порт 80 должен быть открыт

# 4. Создайте директорию для acme-challenge
sudo mkdir -p /var/www/html/.well-known/acme-challenge
sudo chmod -R 755 /var/www/html

# 5. Попробуйте снова
sudo certbot --nginx -d bizcard-crm.ru
```

### Проблема: CORS ошибки после SSL

**Решение:**
Обновите `backend/app/main.py` с HTTPS доменами:
```python
allow_origins=[
    "https://bizcard-crm.ru",
    "https://www.bizcard-crm.ru",
]
```

Пересоберите backend:
```bash
docker compose restart backend
```

### Проблема: Grafana не открывается

**Решение:**
```bash
# Проверьте что Grafana запущен
docker compose ps | grep grafana

# Проверьте порт
curl http://localhost:3001

# Проверьте Nginx конфигурацию для monitoring
sudo nginx -t
```

---

## 📝 Чеклист Финальной Проверки

Перед тем как считать настройку завершенной:

- [ ] DNS записи настроены и работают
- [ ] Nginx установлен и запущен
- [ ] SSL сертификаты получены для всех доменов
- [ ] HTTPS редирект работает (HTTP → HTTPS)
- [ ] SSL оценка A или A+ на SSL Labs
- [ ] Firewall настроен (только 22, 80, 443)
- [ ] Frontend доступен по https://ваш-домен.ru
- [ ] API доступен по https://api.ваш-домен.ru
- [ ] Grafana доступна по https://monitoring.ваш-домен.ru
- [ ] CORS настроен для HTTPS доменов
- [ ] Certbot автообновление работает
- [ ] Docker контейнеры запущены
- [ ] Все функции работают (Login, Upload, OCR)

---

## 🎯 Итоговая Архитектура

```
                      INTERNET
                         ↓
                    VK Cloud VM
                  (87.250.250.123)
                         ↓
                  ┌──────────────┐
                  │   Nginx      │ :80, :443
                  │  (SSL/TLS)   │
                  └──────┬───────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
    Frontend        Backend API      Grafana
    :3000           :8000            :3001
    (Docker)        (Docker)         (Docker)
         ↓               ↓               ↓
    React App      FastAPI        Monitoring
                   + PostgreSQL   + Prometheus
                   + OCR
```

**Домены:**
- `https://bizcard-crm.ru` → Frontend (React)
- `https://api.bizcard-crm.ru` → Backend API
- `https://monitoring.bizcard-crm.ru` → Grafana

**Защита:**
- SSL/TLS сертификаты (Let's Encrypt)
- Firewall (только 22, 80, 443)
- JWT Authentication
- Rate Limiting
- CORS configured

---

## 📚 Полезные Ссылки

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/)
- [Nginx SSL Configuration](https://ssl-config.mozilla.org/)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)
- [VK Cloud Documentation](https://cloud.vk.com/docs/)

---

**Version**: 1.9  
**Last Updated**: 2025-10-19  
**Status**: Production Ready

