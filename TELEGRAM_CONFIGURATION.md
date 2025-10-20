# 📱 Конфигурация Telegram Бота

## ✅ Статус: Настроен и Активен

### 🤖 Информация о Боте

| Параметр | Значение |
|----------|----------|
| **Bot Name** | CRM_bot |
| **Username** | @NewCRMv1Bot |
| **Bot ID** | 8424260030 |
| **Bot Token** | `8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s` |
| **Webhook URL** | `https://ibbase.ru/telegram/webhook` |
| **Server IP** | 95.163.183.25 |
| **Статус** | ✅ Активен |

### 🔗 Быстрый Доступ

**Прямая ссылка на бота:**
```
https://t.me/NewCRMv1Bot
```

### 📋 Возможности Бота

Бот автоматически:
1. ✅ Принимает фото визиток
2. ✅ Распознает текст с помощью OCR
3. ✅ Извлекает контактную информацию:
   - Имя и фамилию
   - Должность
   - Компанию
   - Телефон
   - Email
   - Адрес
4. ✅ Создает новый контакт в CRM
5. ✅ Сохраняет оригинал фото

### 🚀 Как Использовать

#### 1. Запуск Бота
```
1. Откройте Telegram
2. Найдите: @NewCRMv1Bot
3. Нажмите "Start" или отправьте /start
4. Бот поприветствует вас
```

#### 2. Отправка Визитки
```
1. Сделайте фото визитки (или выберите из галереи)
2. Отправьте фото боту
3. Дождитесь подтверждения
4. Контакт автоматически создан!
```

#### 3. Проверка Результата
```
1. Откройте https://ibbase.ru
2. Войдите в систему
3. Новый контакт появится в списке
4. Нажмите на контакт для просмотра деталей
```

### 🔧 Техническая Конфигурация

#### Webhook Configuration
```bash
# Проверить статус webhook
curl "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/getWebhookInfo"

# Установить webhook
curl -X POST "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/setWebhook" \
  -d "url=https://ibbase.ru/telegram/webhook"

# Удалить webhook (для переключения на polling)
curl -X POST "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/deleteWebhook"
```

#### База Данных
```sql
-- Проверить настройки Telegram
SELECT key, value FROM app_settings WHERE key LIKE '%TELEGRAM%';

-- Обновить webhook URL
UPDATE app_settings 
SET value = 'https://ibbase.ru/telegram/webhook' 
WHERE key = 'TELEGRAM_WEBHOOK_URL';

-- Включить/выключить интеграцию
UPDATE app_settings 
SET value = 'true' 
WHERE key = 'TELEGRAM_ENABLED';
```

#### Nginx Configuration
Endpoint уже настроен в `frontend/nginx.conf`:
```nginx
location = /telegram/webhook {
  proxy_pass http://backend:8000/telegram/webhook;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 🔍 Мониторинг и Отладка

#### Просмотр Логов
```bash
# Все Telegram логи
docker compose logs backend -f | grep telegram

# Последние 50 строк
docker compose logs backend --tail 50 | grep telegram

# Ошибки
docker compose logs backend --tail 100 | grep -i "error.*telegram"
```

#### Проверка Работоспособности
```bash
# 1. Проверить бота
curl "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/getMe"

# 2. Проверить webhook
curl "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/getWebhookInfo"

# 3. Проверить endpoint
curl -I https://ibbase.ru/telegram/webhook
# Ожидаемый ответ: HTTP/2 405 (Method Not Allowed) - это нормально!
```

#### Тестирование
```bash
# Отправить тестовое сообщение (через Telegram Web/App)
# 1. Откройте https://t.me/NewCRMv1Bot
# 2. Отправьте /start
# 3. Отправьте любое фото
# 4. Проверьте логи:
docker compose logs backend -f | grep "telegram\|photo"
```

### 📊 Метрики

Система отслеживает:
- Количество полученных сообщений
- Количество обработанных фото
- Успешные/неудачные распознавания
- Время обработки

Метрики доступны в:
- **Prometheus**: http://95.163.183.25:9090
- **Grafana**: http://95.163.183.25:3001

### ⚠️ Troubleshooting

#### Проблема: Бот не отвечает
**Решение:**
```bash
# 1. Проверьте что бот запущен
curl "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/getMe"

# 2. Проверьте webhook
curl "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/getWebhookInfo"

# 3. Проверьте логи backend
docker compose logs backend --tail 100 | grep telegram

# 4. Перезапустите backend
docker compose restart backend
```

#### Проблема: Фото не распознается
**Решение:**
```bash
# 1. Проверьте OCR настройки
docker exec bizcard-db psql -U postgres -d bizcard_crm \
  -c "SELECT key, value FROM app_settings WHERE key LIKE '%OCR%';"

# 2. Проверьте что Tesseract работает
docker exec bizcard-backend tesseract --version

# 3. Проверьте логи OCR
docker compose logs backend -f | grep -i "ocr\|tesseract"
```

#### Проблема: Webhook возвращает ошибку
**Решение:**
```bash
# 1. Проверьте SSL сертификат
curl -v https://ibbase.ru/telegram/webhook 2>&1 | grep "SSL\|certificate"

# 2. Проверьте доступность endpoint
curl -X POST https://ibbase.ru/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# 3. Переустановите webhook
curl -X POST "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/setWebhook" \
  -d "url=https://ibbase.ru/telegram/webhook" \
  -d "drop_pending_updates=true"
```

### 🔐 Безопасность

**Важные замечания:**
1. ⚠️ Никогда не публикуйте Bot Token в открытом виде
2. ✅ Храните токен только в базе данных или .env файле
3. ✅ Используйте HTTPS для webhook (у вас уже настроено)
4. ✅ Регулярно проверяйте webhook на наличие ошибок
5. ⚠️ Ограничьте доступ к endpoint только для Telegram IP

**Рекомендации:**
- Используйте `drop_pending_updates=true` при установке webhook
- Регулярно проверяйте `getWebhookInfo` на наличие ошибок
- Мониторьте `pending_update_count` - если растет, значит есть проблемы

### 📝 История Изменений

**2025-10-20**
- ✅ Исправлен webhook URL: `www.ibbase.ru` → `ibbase.ru`
- ✅ Установлен webhook через Telegram API
- ✅ Проверена работоспособность endpoint
- ✅ Интеграция активирована и работает

**Настроено:**
- Bot Token в базе данных
- Webhook URL на production домен
- HTTPS endpoint в Nginx
- OCR распознавание для русского и английского

### 📞 Поддержка

**Полезные ссылки:**
- Telegram Bot API: https://core.telegram.org/bots/api
- Webhook Guide: https://core.telegram.org/bots/webhooks
- Admin Panel: https://ibbase.ru/admin
- System Settings: https://ibbase.ru/admin → ⚙️ System Settings → ✈️ Telegram

**Команды для быстрого доступа:**
```bash
# Статус
docker compose ps | grep backend

# Логи
docker compose logs backend -f | grep telegram

# Перезапуск
docker compose restart backend

# Проверка
curl "https://api.telegram.org/bot8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s/getWebhookInfo"
```

---

**Создано:** 2025-10-20  
**Обновлено:** 2025-10-20  
**Версия:** v2.5.1  
**Статус:** ✅ Работает

