# 🎛️ Переключатель OCR v1.0 / v2.0 - Быстрый старт

## 📍 Как открыть

**Web UI:**
```
https://ibbase.ru/admin?tab=settings
```

В верхней части страницы увидите секцию **"Версия OCR"** с двумя карточками.

## 🚀 Быстрое переключение

### Вариант 1: Через Web UI (рекомендуется)

1. Откройте `https://ibbase.ru/admin?tab=settings`
2. Найдите секцию "Версия OCR" вверху
3. Кликните на карточку нужной версии
4. Готово! ✅

### Вариант 2: Через API

```bash
# Получить токен администратора
TOKEN="your_admin_token_here"

# Переключить на v1.0 (быстро)
curl -X POST https://ibbase.ru/api/ocr/settings/version \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "v1.0"}'

# Переключить на v2.0 (точно)
curl -X POST https://ibbase.ru/api/ocr/settings/version \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "v2.0"}'
```

### Вариант 3: Через базу данных

```bash
# Подключиться к БД
docker exec -it bizcard-db psql -U bizcard -d bizcard_crm

# Изменить версию
UPDATE app_settings SET value = 'v1.0' WHERE key = 'ocr_version';

# или
UPDATE app_settings SET value = 'v2.0' WHERE key = 'ocr_version';

# Выйти
\q
```

## 📊 Сравнение версий

| Характеристика | OCR v1.0 (Tesseract) | OCR v2.0 (PaddleOCR + AI) |
|----------------|----------------------|---------------------------|
| **Скорость** | ⚡ 1-2 секунды | 🐢 3-5 секунд |
| **Точность** | 60-70% | 80-90% |
| **AI классификация** | ❌ | ✅ LayoutLMv3 |
| **Автоматическая валидация** | ❌ | ✅ |
| **Сохранение в MinIO** | ❌ | ✅ |
| **Автофолбэк при ошибке** | — | ✅ на v1.0 |

## 🎯 Когда использовать

### v1.0 - для скорости:
- ✅ Batch-импорт большого количества карточек
- ✅ Простые визитки только с текстом
- ✅ Когда важна скорость, а не точность
- ✅ При ограниченных ресурсах сервера

### v2.0 - для качества:
- ✅ Сложные визитки с логотипами
- ✅ Когда важна максимальная точность
- ✅ Нужна автоматическая классификация полей
- ✅ Требуется хранение данных для ML обучения

## ✅ Проверка текущей версии

### Способ 1: API (без токена)
```bash
curl https://ibbase.ru/api/ocr/settings/version | jq '.version'
```

### Способ 2: В браузере (Console)
```javascript
fetch('/api/ocr/settings/version')
  .then(r => r.json())
  .then(d => console.log('OCR version:', d.version));
```

### Способ 3: В логах
```bash
# Backend
docker logs bizcard-backend | grep "OCR v"

# Celery
docker logs bizcard-celery-worker | grep "Using OCR"
```

### Способ 4: В базе данных
```bash
docker exec bizcard-db psql -U bizcard -d bizcard_crm \
  -c "SELECT value FROM app_settings WHERE key = 'ocr_version';"
```

## 🔍 Мониторинг

После загрузки визиток проверьте:

**1. Логи Celery:**
```bash
docker logs bizcard-celery-worker 2>&1 | tail -50
```

Вы увидите:
- `🚀 Using OCR v2.0 for filename.jpg` - используется v2.0
- `🔧 Using OCR v1.0 for filename.jpg` - используется v1.0
- `⚠️ OCR v2.0 failed, falling back to v1.0` - автофолбэк

**2. Админ-панель мониторинга:**
```
https://ibbase.ru/admin?tab=monitoring
```

Показывает:
- Метод распознавания
- Время обработки
- Confidence score
- Последние сканирования

## 🐛 Troubleshooting

### Проблема: Не вижу секцию "Версия OCR"

**Решение:**
```bash
# Очистить кэш браузера
Ctrl + Shift + R

# Перезапустить frontend
docker compose restart frontend
```

### Проблема: Версия не меняется

**Решение:**
```bash
# Перезапустить backend и celery
docker compose restart backend celery-worker

# Проверить в БД
docker exec bizcard-db psql -U bizcard -d bizcard_crm \
  -c "SELECT * FROM app_settings WHERE key = 'ocr_version';"
```

### Проблема: 403 Forbidden при смене версии

**Причина:** Endpoint доступен только администраторам

**Решение:** Проверьте роль пользователя:
```bash
curl https://ibbase.ru/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq '.role'
```

Должно быть: `"admin"`

## 📚 Документация

Подробная документация:
- **OCR_VERSION_TOGGLE.md** - Полная документация (411 строк)
- **OCR_TOGGLE_TEST.md** - Инструкции по тестированию (331 строк)
- **OCR_TOGGLE_COMPLETE.md** - Итоговый отчет (490+ строк)
- **OCR_TOGGLE_QUICKSTART.md** - Эта страница

## 💡 Полезные команды

```bash
# Проверить статус сервисов
docker ps --format "table {{.Names}}\t{{.Status}}"

# Перезапустить все сервисы
docker compose restart

# Посмотреть логи backend
docker logs bizcard-backend -f

# Посмотреть логи celery
docker logs bizcard-celery-worker -f

# Проверить версию OCR
curl https://ibbase.ru/api/ocr/settings/version

# Загрузить тестовую визитку
curl -X POST https://ibbase.ru/api/ocr/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@business_card.jpg"
```

## 🎉 Готово!

Теперь вы можете легко переключаться между версиями OCR в зависимости от ваших задач:
- 🏃 **v1.0** - быстро
- 🎯 **v2.0** - точно

**Изменения применяются мгновенно, без перезапуска системы!**

---

**Версия:** 6.1.0  
**Дата:** 27 октября 2025  
**Статус:** ✅ Работает

