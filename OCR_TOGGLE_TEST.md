# Тест переключателя OCR версий

## ✅ Что было сделано

### Backend
1. ✅ Создан API endpoint `/api/ocr/settings/version` для управления версией OCR
2. ✅ Добавлены endpoints:
   - `GET /api/ocr/settings/version` - получить текущую версию и информацию
   - `POST /api/ocr/settings/version` - изменить версию (только admin)
   - `GET /api/ocr/settings/config` - получить детальную конфигурацию OCR
3. ✅ Обновлен `backend/app/api/ocr.py` - проверка версии OCR перед обработкой
4. ✅ Обновлен `backend/app/tasks.py` - проверка версии OCR в Celery задачах (2 места)
5. ✅ Зарегистрирован router в `backend/app/api/__init__.py`

### Frontend
1. ✅ Создан компонент `OCRVersionToggle.js` с красивым UI
2. ✅ Интегрирован в `SystemSettings.js` (вкладка Settings в админ-панели)
3. ✅ Создан экспорт в `frontend/src/components/admin/index.js`

### Особенности
- ✅ Изменения применяются мгновенно (без перезапуска)
- ✅ Автоматический fallback v2.0 → v1.0 при ошибках
- ✅ Хранение настройки в базе данных (таблица `app_settings`)
- ✅ Визуальное отображение текущей версии
- ✅ Детальная информация о возможностях каждой версии
- ✅ Логирование использования версий

## 🧪 Тестирование

### 1. Проверка Web UI

Откройте в браузере:
```
https://ibbase.ru/admin?tab=settings
```

Вы должны увидеть:
- Секцию "Версия OCR" / "OCR Version" в верхней части страницы
- Две карточки: OCR v1.0 и OCR v2.0
- Текущую активную версию выделенную цветом
- Кнопки для переключения версий

**Действия:**
1. Нажмите на карточку "OCR v1.0"
2. Должно появиться уведомление "Версия OCR успешно изменена"
3. Карточка v1.0 должна выделиться серым цветом
4. Нажмите на карточку "OCR v2.0"
5. Карточка v2.0 должна выделиться синим цветом

### 2. Проверка API (через curl)

#### Получить текущую версию (без авторизации)
```bash
curl https://ibbase.ru/api/ocr/settings/version
```

Ожидаемый ответ:
```json
{
  "version": "v2.0",
  "available_versions": ["v1.0", "v2.0"],
  "v1": {...},
  "v2": {...}
}
```

#### Изменить версию (требуется admin токен)
```bash
# Получить токен
TOKEN="YOUR_ADMIN_TOKEN_HERE"

# Установить v1.0
curl -X POST https://ibbase.ru/api/ocr/settings/version \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "v1.0"}'

# Установить v2.0
curl -X POST https://ibbase.ru/api/ocr/settings/version \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "v2.0"}'
```

### 3. Проверка работы OCR

#### Загрузить тестовую визитку через v1.0
```bash
# 1. Установить v1.0
curl -X POST https://ibbase.ru/api/ocr/settings/version \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "v1.0"}'

# 2. Загрузить визитку
curl -X POST https://ibbase.ru/api/ocr/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/business_card.jpg"

# 3. Проверить логи
docker logs bizcard-celery-worker 2>&1 | grep "Using OCR v1.0"
```

#### Загрузить тестовую визитку через v2.0
```bash
# 1. Установить v2.0
curl -X POST https://ibbase.ru/api/ocr/settings/version \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "v2.0"}'

# 2. Загрузить визитку
curl -X POST https://ibbase.ru/api/ocr/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/business_card.jpg"

# 3. Проверить логи
docker logs bizcard-celery-worker 2>&1 | grep "Using OCR v2.0"
```

### 4. Проверка в базе данных

```bash
# Подключиться к БД
docker exec -it bizcard-db psql -U bizcard -d bizcard_crm

# Проверить настройку
SELECT * FROM app_settings WHERE key = 'ocr_version';

# Выйти
\q
```

### 5. Мониторинг

Откройте панель мониторинга:
```
https://ibbase.ru/admin?tab=monitoring
```

После загрузки нескольких карточек вы должны увидеть:
- Метод распознавания (OCR v1.0 или v2.0)
- Время обработки
- Confidence score

## 📊 Ожидаемые результаты

### OCR v1.0 (Tesseract)
- Время обработки: 1-2 секунды
- В логах: `🔧 Using OCR v1.0 for filename.jpg`
- Recognition method: `Tesseract v1.0`

### OCR v2.0 (PaddleOCR + AI)
- Время обработки: 3-5 секунд
- В логах: `🚀 Using OCR v2.0 for filename.jpg`
- Recognition method: `PaddleOCR v2.0 + LayoutLMv3`
- Дополнительно: validation applied, saved to MinIO

### Автоматический Fallback
Если v2.0 не сможет обработать изображение:
- В логах: `⚠️ OCR v2.0 failed, falling back to v1.0`
- Следующая строка: `✅ OCR v1.0 (Tesseract) fallback successful`
- Карточка все равно будет распознана

## 🔍 Проверка логов

### Backend
```bash
# Проверить использование OCR
docker logs bizcard-backend 2>&1 | grep -E "OCR v[12].0"

# Проверить ошибки
docker logs bizcard-backend 2>&1 | grep -i error | tail -20
```

### Celery Worker
```bash
# Проверить использование OCR
docker logs bizcard-celery-worker 2>&1 | grep -E "Using OCR|OCR.*completed"

# Проверить fallback
docker logs bizcard-celery-worker 2>&1 | grep "fallback"
```

### Frontend (в браузере)
```javascript
// Откройте консоль браузера (F12) и выполните:
fetch('/api/ocr/settings/version')
  .then(r => r.json())
  .then(d => console.log('Current OCR version:', d.version));
```

## 🐛 Troubleshooting

### Проблема: Кнопка не работает в UI
**Решение:**
```bash
# Перезапустить frontend
docker compose restart frontend

# Проверить логи frontend
docker logs bizcard-frontend
```

### Проблема: API возвращает 404
**Решение:**
```bash
# Перезапустить backend
docker compose restart backend

# Проверить что router зарегистрирован
docker logs bizcard-backend 2>&1 | grep "ocr/settings"
```

### Проблема: Версия не меняется
**Решение:**
```bash
# Проверить в БД
docker exec bizcard-db psql -U bizcard -d bizcard_crm \
  -c "SELECT * FROM app_settings WHERE key = 'ocr_version';"

# Перезапустить Celery
docker compose restart celery-worker

# Проверить что настройка применяется
docker logs bizcard-celery-worker 2>&1 | tail -50
```

### Проблема: 403 Forbidden при изменении версии
**Причина:** Endpoint доступен только администраторам

**Решение:**
```bash
# Проверить роль пользователя
curl https://ibbase.ru/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq '.role'

# Должно быть: "admin"
```

## ✨ Дополнительные фичи

### Просмотр конфигурации
```bash
curl https://ibbase.ru/api/ocr/settings/config \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Мониторинг производительности
```bash
# Среднее время обработки за последние 24 часа
curl https://ibbase.ru/api/monitoring/dashboard \
  -H "Authorization: Bearer $TOKEN" | jq '.ocr_stats'
```

### Сравнение версий
```bash
# Обработать 10 карточек через v1.0
# Обработать 10 карточек через v2.0
# Сравнить точность и скорость в админ-панели
```

## 📝 Чеклист тестирования

- [ ] Открыть админ-панель → Settings
- [ ] Увидеть секцию "Версия OCR"
- [ ] Переключиться на v1.0
- [ ] Загрузить визитку
- [ ] Проверить что использовался v1.0 (логи)
- [ ] Переключиться на v2.0
- [ ] Загрузить визитку
- [ ] Проверить что использовался v2.0 (логи)
- [ ] Проверить мониторинг в админ-панели
- [ ] Проверить API endpoint через curl
- [ ] Проверить настройку в базе данных

---

**Статус:** ✅ Готово к тестированию  
**Дата:** 27 октября 2025  
**Версия:** 6.1.0

