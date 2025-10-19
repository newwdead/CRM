# 📱 Telegram интеграция для BizCard CRM

## ✅ Статус: Настроено и работает!

Telegram бот настроен и работает через **polling** (получение сообщений каждую секунду).

---

## 🤖 Как это работает

1. Вы отправляете **фото визитной карточки** боту в Telegram
2. Скрипт `telegram_polling.py` получает обновление
3. Фото скачивается и обрабатывается через **Tesseract OCR** (или Parsio)
4. Распознанные данные автоматически создают новый контакт в CRM
5. Фото сохраняется в `uploads/`

---

## 📊 Текущие настройки

| Параметр | Значение |
|----------|----------|
| **Bot Token** | `8424260030:AAE...Pm5s` |
| **Статус** | ✅ Включен (enabled: true) |
| **Разрешенные чаты** | Все (пусто = любой чат) |
| **OCR провайдер** | Tesseract (локальный) |
| **Режим работы** | Polling (не webhook) |

---

## 🚀 Управление сервисом

### Проверить статус
```bash
sudo systemctl status telegram-polling
```

### Остановить
```bash
sudo systemctl stop telegram-polling
```

### Запустить
```bash
sudo systemctl start telegram-polling
```

### Перезапустить
```bash
sudo systemctl restart telegram-polling
```

### Логи
```bash
sudo journalctl -u telegram-polling -f
```

---

## 🔧 Изменение настроек

### 1. Изменить Telegram токен

Отредактируйте файл сервиса:
```bash
sudo nano /etc/systemd/system/telegram-polling.service
```

Измените строку `Environment="TELEGRAM_TOKEN=..."` и перезапустите:
```bash
sudo systemctl daemon-reload
sudo systemctl restart telegram-polling
```

### 2. Ограничить разрешенные чаты

Через Web UI в настройках Telegram или через API:
```bash
curl -X PUT http://localhost:8000/settings/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "token": "ваш_токен",
    "allowed_chats": "123456789,987654321",
    "provider": "tesseract"
  }'
```

### 3. Сменить OCR провайдер на Parsio

```bash
curl -X PUT http://localhost:8000/settings/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "token": "ваш_токен",
    "allowed_chats": "",
    "provider": "parsio"
  }'
```

---

## 📝 Ручной запуск (для тестирования)

Остановите сервис и запустите вручную:
```bash
sudo systemctl stop telegram-polling
cd /home/ubuntu/fastapi-bizcard-crm-ready
python3 telegram_polling.py
```

Нажмите `Ctrl+C` для остановки.

---

## 🔄 Webhook vs Polling

### Текущий режим: **Polling** ✅

**Преимущества:**
- ✅ Работает везде (не нужен публичный IP)
- ✅ Не требует SSL сертификата
- ✅ Проще настроить
- ✅ Подходит для dev окружения

**Недостатки:**
- ⚠️ Небольшая задержка (1-2 секунды)
- ⚠️ Постоянно опрашивает Telegram API

### Альтернатива: **Webhook**

Для production с публичным IP и доменом можно настроить webhook:

```bash
# Установить webhook
TELEGRAM_TOKEN="ваш_токен"
curl -F "url=https://ваш-домен.com:8443/telegram/webhook" \
     -F "certificate=@/etc/nginx/certs/selfsigned.crt" \
     "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook"

# Остановить polling
sudo systemctl stop telegram-polling
sudo systemctl disable telegram-polling
```

**Требования для webhook:**
- ✅ Публичный IP адрес
- ✅ Открытый порт 8443 (или 443, 80, 88)
- ✅ Валидный SSL сертификат (Let's Encrypt или самоподписанный)

---

## 📂 Файлы

| Файл | Описание |
|------|----------|
| `telegram_polling.py` | Скрипт для получения обновлений |
| `telegram-polling.service` | Systemd сервис |
| `/etc/systemd/system/telegram-polling.service` | Установленный сервис |

---

## ❓ Частые вопросы

### Фотографии не обрабатываются

1. Проверьте статус сервиса:
   ```bash
   sudo systemctl status telegram-polling
   ```

2. Проверьте логи:
   ```bash
   sudo journalctl -u telegram-polling -f
   ```

3. Проверьте настройки:
   ```bash
   curl http://localhost:8000/settings/telegram
   ```

### Как узнать Chat ID?

Отправьте `/start` боту и проверьте логи:
```bash
sudo journalctl -u telegram-polling -f
```

Вы увидите строки вида: `Chat: 123456789`

### Tesseract плохо распознает текст

Смените провайдер на Parsio (cloud OCR с лучшей точностью):
```bash
curl -X PUT http://localhost:8000/settings/telegram \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "provider": "parsio"}'
```

Не забудьте настроить `PARSIO_API_KEY` в `.env`.

---

## 🎉 Готово!

Теперь просто отправляйте фото визиток боту в Telegram, и они автоматически появятся в CRM! 📸➡️💼

