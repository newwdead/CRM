# 🔍 OCR Провайдеры - Настройка и использование

## 📋 Содержание

- [О системе](#о-системе)
- [Доступные провайдеры](#доступные-провайдеры)
- [Автоматический Fallback](#автоматический-fallback)
- [Настройка](#настройка)
- [Использование через API](#использование-через-api)
- [Сравнение провайдеров](#сравнение-провайдеров)
- [Troubleshooting](#troubleshooting)

---

## 🎯 О системе

BizCard CRM v1.6+ использует продвинутую систему OCR с поддержкой нескольких провайдеров и автоматическим fallback. Если один провайдер не сработал, система автоматически попробует следующий по приоритету.

### Архитектура

```
┌─────────────────┐
│   OCRManager    │ ← Управляет всеми провайдерами
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    ▼         ▼         ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│Parsio│  │Google│  │Tesser│  │Future│
│      │  │Vision│  │ act  │  │ ...  │
└──────┘  └──────┘  └──────┘  └──────┘
Priority 1  Priority 2  Priority 3
```

---

## 📦 Доступные провайдеры

### 1. **Tesseract** (Локальный, бесплатный)

✅ **Преимущества:**
- Бесплатный
- Работает локально (не требует интернета)
- Поддержка многих языков (русский + английский)
- Быстрый

⚠️ **Недостатки:**
- Средняя точность (особенно на сложных изображениях)
- Требует качественного изображения
- Может не распознать рукописный текст

**Приоритет:** 3 (используется последним)  
**Уверенность:** ~70%  
**Статус:** ✅ Включен по умолчанию

#### Настройка:

```ini
# .env
TESSERACT_LANGS=eng+rus
```

Tesseract уже установлен в Docker контейнере. Дополнительная настройка не требуется.

---

### 2. **Parsio** (Облачный, платный)

✅ **Преимущества:**
- Высокая точность распознавания
- Специально обучен для визитных карточек
- Структурированный вывод данных
- Поддержка сложных макетов

⚠️ **Недостатки:**
- Требует подписку (платный)
- Зависит от интернета
- Медленнее чем Tesseract

**Приоритет:** 1 (используется первым)  
**Уверенность:** ~90%  
**Статус:** ⚙️ Требует настройки

#### Настройка:

1. Создайте аккаунт на https://parsio.io/
2. Создайте mailbox для визитных карточек
3. Получите API ключ
4. Настройте переменные окружения:

```ini
# .env
PARSIO_API_KEY=your_api_key_here
PARSIO_API_URL=https://api.parsio.io/mailboxes/<mailbox_id>/upload
PARSIO_DOCUMENT_URL_TEMPLATE=https://api.parsio.io/docs/{id}
PARSIO_AUTH_HEADER_NAME=X-API-Key
PARSIO_AUTH_HEADER_VALUE={key}
PARSIO_TIMEOUT=45
PARSIO_POLL_INTERVAL=2.0
PARSIO_POLL_MAX_ATTEMPTS=20
```

5. Перезапустите backend:
```bash
docker compose restart backend
```

---

### 3. **Google Cloud Vision API** (Облачный, платный)

✅ **Преимущества:**
- Очень высокая точность
- Отличное распознавание текста на любых языках
- Хорошо работает с рукописным текстом
- Мощные возможности обработки изображений

⚠️ **Недостатки:**
- Требует Google Cloud аккаунт
- Платный (но есть бесплатный лимит)
- Зависит от интернета
- Требует настройки API

**Приоритет:** 2 (используется вторым)  
**Уверенность:** ~95%  
**Статус:** ⚙️ Требует настройки

#### Настройка:

1. Создайте проект в Google Cloud Console
2. Включите Cloud Vision API
3. Создайте API ключ (рекомендуется ограничить по IP)
4. Настройте переменную окружения:

```ini
# .env
GOOGLE_VISION_API_KEY=your_google_api_key_here
```

5. Перезапустите backend:
```bash
docker compose restart backend
```

**Полная инструкция:**
1. Откройте https://console.cloud.google.com/
2. Создайте новый проект или выберите существующий
3. Включите Cloud Vision API:
   - Перейдите в "APIs & Services" → "Library"
   - Найдите "Cloud Vision API"
   - Нажмите "Enable"
4. Создайте API ключ:
   - Перейдите в "APIs & Services" → "Credentials"
   - Нажмите "Create Credentials" → "API key"
   - Скопируйте ключ
   - (Рекомендуется) Ограничьте ключ по IP и API
5. Добавьте ключ в `.env` файл

---

## 🔄 Автоматический Fallback

### Как это работает

Система пробует провайдеры в порядке приоритета:

```
1️⃣ Parsio (если настроен) → высокая точность
                ↓ (если не сработал)
2️⃣ Google Vision (если настроен) → очень высокая точность
                ↓ (если не сработал)
3️⃣ Tesseract (всегда доступен) → средняя точность
```

### Когда срабатывает fallback?

- Провайдер не настроен (нет API ключа)
- Сетевая ошибка
- Ошибка API (rate limit, timeout)
- Провайдер не смог извлечь данные

### Пример работы

```
📸 Пользователь загружает визитку

🔍 OCRManager пробует Parsio...
   ❌ Ошибка: rate limit exceeded

🔍 OCRManager пробует Google Vision...
   ❌ Не настроен (нет API ключа)

🔍 OCRManager пробует Tesseract...
   ✅ Успешно распознано!

📊 Результат сохранен с информацией:
   Provider: Tesseract
   Confidence: 0.70
```

---

## ⚙️ Настройка

### Режим 'auto' (рекомендуется)

По умолчанию используется режим `auto` - система автоматически выбирает лучший доступный провайдер:

```bash
# Через API
curl -X POST http://localhost:8000/upload/ \
  -F "file=@card.jpg" \
  -F "provider=auto"

# Через Telegram настройки
curl -X PUT http://localhost:8000/settings/telegram \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "provider": "auto"}'
```

### Выбор конкретного провайдера

Можно указать конкретный провайдер:

```bash
# Tesseract
curl -X POST http://localhost:8000/upload/ \
  -F "file=@card.jpg" \
  -F "provider=tesseract"

# Parsio
curl -X POST http://localhost:8000/upload/ \
  -F "file=@card.jpg" \
  -F "provider=parsio"

# Google Vision
curl -X POST http://localhost:8000/upload/ \
  -F "file=@card.jpg" \
  -F "provider=google"
```

**Примечание:** Если указанный провайдер не доступен или не сработал, система автоматически перейдет к следующему по приоритету.

---

## 📖 Использование через API

### Получить список доступных провайдеров

```bash
GET /ocr/providers
```

**Ответ:**
```json
{
  "available": ["Tesseract", "Parsio", "Google Vision"],
  "details": [
    {
      "name": "Parsio",
      "priority": 1,
      "available": true
    },
    {
      "name": "Google Vision",
      "priority": 2,
      "available": false
    },
    {
      "name": "Tesseract",
      "priority": 3,
      "available": true
    }
  ]
}
```

### Загрузить визитку с OCR

```bash
POST /upload/?provider=auto
Content-Type: multipart/form-data

file: <binary image>
```

**Ответ:**
```json
{
  "id": 123,
  "full_name": "Иван Иванов",
  "company": "ООО Компания",
  "email": "ivan@company.ru",
  "phone": "+7 (123) 456-78-90",
  "ocr_provider": "Parsio",
  "ocr_confidence": 0.9
}
```

### Настройка Telegram

```bash
# Получить настройки
GET /settings/telegram

# Обновить настройки
PUT /settings/telegram
Content-Type: application/json

{
  "enabled": true,
  "token": "bot_token",
  "allowed_chats": "123,456",
  "provider": "auto"
}
```

---

## 📊 Сравнение провайдеров

| Параметр | Tesseract | Parsio | Google Vision |
|----------|-----------|--------|---------------|
| **Цена** | Бесплатно | $19+/мес | $1.50/1000 запросов* |
| **Точность** | 70% | 90% | 95% |
| **Скорость** | Быстро | Средне | Быстро |
| **Интернет** | Не требуется | Требуется | Требуется |
| **Языки** | Много | Много | Все |
| **Рукописный текст** | Плохо | Хорошо | Отлично |
| **Сложные макеты** | Средне | Отлично | Отлично |
| **Настройка** | Не требуется | Средняя | Средняя |
| **Приоритет** | 3 (последний) | 1 (первый) | 2 |

\* Google Vision: первые 1000 запросов/месяц бесплатно

### Рекомендации по выбору

**Для development:**
- ✅ Tesseract - достаточно для тестирования

**Для production (малый объем):**
- ✅ Tesseract + Google Vision (бесплатный лимит)

**Для production (большой объем):**
- ✅ Parsio + Tesseract (fallback)
- ✅ Google Vision + Tesseract (fallback)

**Максимальная точность:**
- ✅ Parsio → Google Vision → Tesseract (auto режим)

---

## 🐛 Troubleshooting

### Провайдер не работает

1. **Проверьте настройки:**
```bash
curl http://localhost:8000/ocr/providers
```

2. **Проверьте переменные окружения:**
```bash
docker compose exec backend env | grep -E "PARSIO|GOOGLE"
```

3. **Проверьте логи:**
```bash
docker compose logs backend | grep OCR
```

### Parsio ошибки

**403 Forbidden:**
- Проверьте API ключ
- Убедитесь что подписка активна

**404 Not Found:**
- Проверьте `PARSIO_API_URL` (должен содержать mailbox ID)
- Проверьте `PARSIO_DOCUMENT_URL_TEMPLATE`

**Rate limit:**
- Увеличьте тарифный план Parsio
- Или используйте fallback на другие провайдеры

### Google Vision ошибки

**403 Forbidden:**
- Проверьте API ключ
- Убедитесь что Cloud Vision API включен
- Проверьте ограничения ключа (IP, API)

**429 Too Many Requests:**
- Вы превысили лимит (1000 бесплатных запросов/месяц)
- Включите биллинг в Google Cloud

**Billing not enabled:**
- Включите биллинг в Google Cloud Console
- Но первые 1000 запросов все равно бесплатны!

### Все провайдеры не работают

```bash
# Проверить что Tesseract установлен
docker compose exec backend tesseract --version

# Проверить языки
docker compose exec backend tesseract --list-langs

# Должны быть: eng, rus

# Пересобрать контейнер
docker compose build backend
docker compose restart backend
```

---

## 💡 Советы по оптимизации

### Для лучшей точности

1. **Качество изображения:**
   - Используйте высокое разрешение (минимум 1000px)
   - Хорошее освещение
   - Минимум теней и бликов

2. **Формат файла:**
   - JPEG или PNG
   - Избегайте сильного сжатия

3. **Выбор провайдера:**
   - Для сложных визиток → Parsio или Google Vision
   - Для простых → Tesseract достаточно

### Для экономии средств

1. **Используйте режим 'auto':**
   - Parsio/Google сработает только если Tesseract не смог

2. **Tesseract для предпросмотра:**
   - Быстро и бесплатно
   - Затем можно пересканировать через premium провайдер

3. **Google Vision:**
   - Используйте бесплатный лимит (1000/мес)
   - Включайте только для важных карточек

---

## 📚 Дополнительные ресурсы

- [Parsio Documentation](https://parsio.io/docs/)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
- [Tesseract Documentation](https://tesseract-ocr.github.io/)

---

**Готово! OCR провайдеры настроены и готовы к работе! 🎉**

