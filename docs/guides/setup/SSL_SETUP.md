# SSL Настройка / SSL Setup

## 🔒 Самоподписанный SSL сертификат установлен

Для вашего проекта был создан самоподписанный SSL сертификат для HTTPS доступа и Telegram webhook.

### 📋 Информация о сертификате

- **Расположение**: `/etc/nginx/certs/`
- **Файлы**:
  - `selfsigned.crt` - SSL сертификат (публичный ключ)
  - `selfsigned.key` - Приватный ключ
- **CN (Common Name)**: localhost
- **Организация**: BizCard CRM
- **Страна**: RU
- **Срок действия**: 365 дней (до 19 октября 2026)

### 🌐 Доступ к приложению

#### HTTP (незащищенный)
```
http://localhost:3000
```

#### HTTPS (защищенный, самоподписанный)
```
https://localhost:8443
```

**Примечание**: Браузер покажет предупреждение о безопасности, так как сертификат самоподписанный. Это нормально для локальной разработки. Нажмите "Дополнительно" → "Перейти на сайт".

### 📱 Telegram Webhook

Для настройки Telegram webhook используйте HTTPS URL:
```
https://your-domain.com:8443/telegram/webhook
```

Замените `your-domain.com` на ваш реальный домен или IP адрес.

### 🔄 Пересоздание сертификата

Если нужно создать новый сертификат (например, с другим CN):

```bash
# Удалить старые сертификаты
sudo rm /etc/nginx/certs/selfsigned.*

# Создать новые (замените localhost на ваш домен)
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/nginx/certs/selfsigned.key \
  -out /etc/nginx/certs/selfsigned.crt \
  -days 365 \
  -subj "/CN=your-domain.com/O=BizCard CRM/C=RU"

# Перезапустить frontend
docker compose restart frontend
```

### 🏢 Использование настоящего SSL сертификата (Production)

Для production рекомендуется использовать настоящий SSL сертификат от Let's Encrypt:

1. Установите certbot:
```bash
sudo apt install certbot python3-certbot-nginx
```

2. Получите сертификат:
```bash
sudo certbot certonly --standalone -d your-domain.com
```

3. Обновите `docker-compose.yml`:
```yaml
frontend:
  volumes:
    - /etc/letsencrypt/live/your-domain.com:/etc/nginx/certs:ro
```

4. Обновите `frontend/nginx.conf`:
```nginx
ssl_certificate     /etc/nginx/certs/fullchain.pem;
ssl_certificate_key /etc/nginx/certs/privkey.pem;
```

### 🛠️ Проверка сертификата

```bash
# Информация о сертификате
openssl x509 -in /etc/nginx/certs/selfsigned.crt -noout -text

# Проверка соединения
openssl s_client -connect localhost:8443 -showcerts
```

### 📝 Примечания

- Самоподписанный сертификат **НЕ** подходит для публичного production сервера
- Браузеры будут показывать предупреждения о небезопасном соединении
- Для production используйте сертификат от доверенного CA (Let's Encrypt, Comodo, etc.)
- Telegram Bot API требует настоящий SSL сертификат для webhook в production

