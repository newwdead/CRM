# 🔒 Быстрая настройка HTTPS для ibbase.ru

## Почему сейчас HTTP?

В данный момент приложение работает по **HTTP** (незащищённое соединение) на порту 3000. Это временная конфигурация для разработки и тестирования.

## ⚠️ Проблемы с HTTP в production:

1. **Незащищённая передача данных** - логины, пароли, данные контактов передаются открытым текстом
2. **Telegram webhook требует HTTPS** - боты Telegram работают только через HTTPS
3. **Браузеры помечают сайт как "Небезопасный"**
4. **PWA не работает** без HTTPS
5. **Некоторые API (геолокация, камера) требуют HTTPS**

---

## 🚀 Настройка HTTPS с Let's Encrypt (бесплатный SSL)

### Шаг 1: Убедитесь, что домен делегирован

```bash
# Проверьте, что домен указывает на ваш сервер
nslookup ibbase.ru
# Должен вернуть: 95.163.183.25
```

### Шаг 2: Установите Certbot

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

### Шаг 3: Настройте Nginx для домена

```bash
# Создайте конфигурацию для ibbase.ru
sudo nano /etc/nginx/sites-available/ibbase.ru
```

Добавьте:

```nginx
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name ibbase.ru www.ibbase.ru;
    
    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other requests to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name ibbase.ru www.ibbase.ru;
    
    # SSL certificates (will be added by Certbot)
    ssl_certificate /etc/letsencrypt/live/ibbase.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ibbase.ru/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    client_max_body_size 20m;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Files (images)
    location /files/ {
        proxy_pass http://localhost:8000/files/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Telegram webhook
    location /telegram/webhook {
        proxy_pass http://localhost:8000/telegram/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Шаг 4: Активируйте конфигурацию

```bash
# Создайте директорию для Let's Encrypt
sudo mkdir -p /var/www/certbot

# Активируйте сайт
sudo ln -s /etc/nginx/sites-available/ibbase.ru /etc/nginx/sites-enabled/

# Проверьте конфигурацию
sudo nginx -t

# Перезапустите Nginx
sudo systemctl restart nginx
```

### Шаг 5: Получите SSL сертификат

```bash
# Получите сертификат для ibbase.ru
sudo certbot --nginx -d ibbase.ru -d www.ibbase.ru
```

Certbot автоматически:
- Получит сертификат
- Обновит конфигурацию Nginx
- Настроит автопродление (через cron)

### Шаг 6: Откройте порты 80 и 443

```bash
# Откройте HTTP (для редиректа)
sudo ufw allow 80/tcp

# Откройте HTTPS
sudo ufw allow 443/tcp

# Проверьте правила
sudo ufw status
```

### Шаг 7: Обновите docker-compose.yml

```yaml
backend:
  environment:
    - USE_HTTPS=true
    - DOMAIN=ibbase.ru
    - SERVER_HOST=ibbase.ru
```

```bash
# Перезапустите backend
docker compose up -d backend
```

### Шаг 8: Настройте Telegram webhook

```bash
# Установите новый webhook с HTTPS
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://ibbase.ru/telegram/webhook",
    "allowed_updates": ["message", "photo"]
  }'
```

---

## 🔄 Автоматическое продление сертификата

Certbot автоматически создаёт cron job для продления:

```bash
# Проверьте автопродление
sudo certbot renew --dry-run
```

Сертификаты Let's Encrypt действуют **90 дней** и автоматически продлеваются за 30 дней до истечения.

---

## ✅ Проверка HTTPS

После настройки проверьте:

```bash
# 1. SSL сертификат
curl -I https://ibbase.ru

# 2. Редирект HTTP → HTTPS
curl -I http://ibbase.ru

# 3. Telegram webhook
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

Откройте в браузере:
- https://ibbase.ru - должен открыться с зелёным замком 🔒

---

## 📊 Что изменится после HTTPS:

✅ **Безопасность**: Все данные шифруются  
✅ **Telegram бот**: Webhook начнёт работать  
✅ **SEO**: Google предпочитает HTTPS сайты  
✅ **PWA**: Progressive Web App станет доступен  
✅ **Доверие**: Браузер покажет зелёный замок  
✅ **Современные API**: Геолокация, камера и т.д.  

---

## 🛠️ Устранение проблем

### Ошибка: "Port 80 already in use"

```bash
# Остановите старый Nginx
sudo systemctl stop nginx

# Или проверьте, что использует порт 80
sudo lsof -i :80
```

### Ошибка: "DNS validation failed"

```bash
# Убедитесь, что домен делегирован
dig ibbase.ru +short
# Должен вернуть: 95.163.183.25

# Подождите 5-10 минут после изменения DNS
```

### Сертификат не продлевается автоматически

```bash
# Проверьте cron
sudo systemctl status certbot.timer

# Вручную продлите
sudo certbot renew
```

---

## 📚 Полная документация

Для подробной инструкции см. [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)

---

## 🎯 Следующий шаг

После настройки HTTPS вернитесь в Admin Panel → System Settings и обновите:
- **Telegram Webhook URL**: `https://ibbase.ru/telegram/webhook`
- **Domain**: `ibbase.ru`
- **USE_HTTPS**: `true`

