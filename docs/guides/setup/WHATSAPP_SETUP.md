# WhatsApp Business API Integration Setup

## Обзор

ibbase интегрирован с WhatsApp Business API для автоматической обработки визиток, отправленных через WhatsApp.

### Возможности

- ✅ Автоматическое создание контактов из фото визиток
- ✅ Поддержка QR-кодов и OCR
- ✅ Текстовые команды (/start, /help, /status)
- ✅ Отправка сообщений через API

---

## Требования

1. **WhatsApp Business Account**
   - Зарегистрируйтесь на [Meta for Developers](https://developers.facebook.com/)
   - Создайте Business Account
   - Добавьте WhatsApp Business product

2. **Публичный HTTPS endpoint**
   - WhatsApp требует HTTPS для webhooks
   - Используйте домен с SSL сертификатом (Let's Encrypt)
   - Или ngrok для тестирования

---

## Шаг 1: Получить учетные данные WhatsApp

### 1.1 Создайте приложение Meta

1. Перейдите на [Meta for Developers](https://developers.facebook.com/)
2. Нажмите **"Create App"**
3. Выберите **"Business"** тип приложения
4. Заполните информацию о приложении

### 1.2 Добавьте WhatsApp Product

1. В Dashboard приложения выберите **"Add Product"**
2. Найдите **"WhatsApp"** и нажмите **"Set Up"**

### 1.3 Получите учетные данные

В разделе WhatsApp **"API Setup"**:

- **Phone Number ID** - ID номера телефона (например: `123456789012345`)
- **Access Token** - Токен доступа (временный токен для тестирования)
- **Webhook Verify Token** - Создайте свой собственный токен (например: `ibbase_verify_token_2024`)

---

## Шаг 2: Настройте Webhook

### 2.1 URL для Webhook

Ваш webhook URL:
```
https://your-domain.com/api/whatsapp/webhook
```

Замените `your-domain.com` на ваш реальный домен.

### 2.2 Настройте Webhook в Meta Dashboard

1. В разделе WhatsApp **"Configuration"** найдите **"Webhooks"**
2. Нажмите **"Edit"**
3. Введите:
   - **Callback URL**: `https://your-domain.com/api/whatsapp/webhook`
   - **Verify Token**: Ваш `WHATSAPP_VERIFY_TOKEN` (например: `ibbase_verify_token_2024`)
4. Нажмите **"Verify and Save"**

### 2.3 Подпишитесь на события

В разделе **"Webhook Fields"** подпишитесь на:
- ✅ **messages** - получение входящих сообщений

---

## Шаг 3: Настройте переменные окружения

### 3.1 Создайте `.env` файл

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
nano .env
```

### 3.2 Добавьте WhatsApp конфигурацию

```env
# WhatsApp Business API
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_PHONE_ID=ваш_phone_number_id
WHATSAPP_ACCESS_TOKEN=ваш_access_token
WHATSAPP_VERIFY_TOKEN=ibbase_verify_token_2024
```

### 3.3 Перезапустите контейнеры

```bash
docker compose down
docker compose up -d
```

---

## Шаг 4: Тестирование

### 4.1 Проверьте webhook

```bash
curl -X GET "https://your-domain.com/api/whatsapp/webhook?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=ibbase_verify_token_2024"
```

Должен вернуть: `test123`

### 4.2 Отправьте тестовое сообщение

1. Откройте WhatsApp на вашем телефоне
2. Отправьте сообщение `/start` на номер WhatsApp Business
3. Получите приветственное сообщение
4. Отправьте фото визитки
5. Получите подтверждение "✅ Визитка получена!"
6. Проверьте контакты в ibbase

---

## Команды WhatsApp

Пользователи могут отправлять следующие команды:

- `/start` или `/help` - Показать справку
- `/status` - Показать статус системы
- **Отправить фото** - Автоматически обработать визитку

---

## Получение постоянного токена доступа

Временный токен истекает через 24 часа. Для production используйте System User Token:

1. В Business Settings создайте **System User**
2. Назначьте роли для WhatsApp
3. Сгенерируйте **Permanent Access Token**
4. Используйте этот токен в `WHATSAPP_ACCESS_TOKEN`

---

## Мониторинг

### Проверка логов

```bash
# Backend logs
docker logs bizcard-backend --tail 100 -f

# Webhook события
grep "WhatsApp webhook" /var/log/bizcard/*.log
```

### Prometheus метрики

WhatsApp использует метрику `telegram_messages_counter`:
- `telegram_messages_counter{status="success"}` - успешные обработки
- `telegram_messages_counter{status="failed"}` - ошибки

---

## Troubleshooting

### Webhook не работает

1. Проверьте, что домен доступен через HTTPS
2. Проверьте WHATSAPP_VERIFY_TOKEN
3. Проверьте логи: `docker logs bizcard-backend`

### Сообщения не обрабатываются

1. Проверьте WHATSAPP_ACCESS_TOKEN
2. Проверьте, что Webhook подписан на "messages"
3. Проверьте логи Celery: `docker logs bizcard-celery-worker`

### Не отправляются сообщения

1. Проверьте WHATSAPP_PHONE_ID и WHATSAPP_ACCESS_TOKEN
2. Проверьте, что номер телефона зарегистрирован в WhatsApp Business
3. Проверьте rate limits WhatsApp API

---

## API Endpoints

### Webhook (GET)
```
GET /api/whatsapp/webhook
```
Используется Meta для верификации webhook.

### Webhook (POST)
```
POST /api/whatsapp/webhook
```
Получает входящие сообщения от WhatsApp.

### Отправка сообщения (Admin)
```
POST /api/whatsapp/send
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "to": "79001234567",
  "message": "Привет! Это тестовое сообщение."
}
```

---

## Безопасность

- ✅ Webhook token проверяется при верификации
- ✅ HTTPS обязателен для production
- ✅ Access token хранится в environment variables
- ✅ Только админы могут отправлять сообщения через API

---

## Ограничения WhatsApp API

- **Rate Limits**: 1000 сообщений в секунду (Free tier)
- **Message Templates**: Требуются для проактивных сообщений
- **24-hour Window**: Ответы на пользовательские сообщения разрешены в течение 24 часов

---

## Дополнительные ресурсы

- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Meta for Developers](https://developers.facebook.com/)
- [WhatsApp Business Platform](https://business.whatsapp.com/)

