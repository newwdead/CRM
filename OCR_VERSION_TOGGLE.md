# Переключатель Версий OCR v1.0 / v2.0

## 📋 Обзор

Добавлена возможность переключения между версиями OCR в админ-панели без перезапуска системы.

## ✨ Возможности

### OCR v1.0 (Tesseract)
- **Скорость:** Быстрая (1-2 секунды)
- **Точность:** 60-70%
- **Технологии:**
  - Tesseract OCR
  - Базовое распознавание текста
  - Поддержка нескольких языков

### OCR v2.0 (PaddleOCR + AI)
- **Скорость:** Средняя (3-5 секунд)
- **Точность:** 80-90%
- **Технологии:**
  - PaddleOCR для распознавания текста
  - LayoutLMv3 для AI-классификации полей
  - Автоматическая валидация и коррекция данных
  - Сохранение в MinIO
  - Автоматический fallback на v1.0 при ошибках

## 🎛️ Использование

### Веб-интерфейс

1. Откройте админ-панель: **https://ibbase.ru/admin**
2. Перейдите на вкладку **"Настройки"** (⚙️ Settings)
3. В самом верху увидите секцию **"Версия OCR"**
4. Выберите нужную версию, кликнув на карточку или кнопку "Выбрать"

### API

#### Получить текущую версию OCR

```bash
curl -X GET "https://ibbase.ru/api/ocr/settings/version" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Ответ:**
```json
{
  "version": "v2.0",
  "available_versions": ["v1.0", "v2.0"],
  "v1": {
    "name": "OCR v1.0 (Tesseract)",
    "description": "Classic Tesseract OCR",
    "speed": "Fast (1-2s)",
    "accuracy": "60-70%",
    "features": ["Basic text recognition", "Multiple languages"]
  },
  "v2": {
    "name": "OCR v2.0 (PaddleOCR + LayoutLMv3)",
    "description": "AI-powered OCR with field classification",
    "speed": "Medium (3-5s)",
    "accuracy": "80-90%",
    "features": [...]
  }
}
```

#### Изменить версию OCR

```bash
curl -X POST "https://ibbase.ru/api/ocr/settings/version" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "v1.0"}'
```

**Ответ:**
```json
{
  "success": true,
  "version": "v1.0",
  "message": "OCR version set to v1.0",
  "restart_required": false
}
```

#### Получить детальную конфигурацию OCR

```bash
curl -X GET "https://ibbase.ru/api/ocr/settings/config" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔧 Технические детали

### Backend изменения

#### Новые файлы:
- `backend/app/api/ocr_settings.py` - API для управления версией OCR

#### Обновленные файлы:
- `backend/app/api/__init__.py` - регистрация нового router
- `backend/app/api/ocr.py` - проверка версии OCR перед обработкой
- `backend/app/tasks.py` - проверка версии OCR в Celery задачах

### Frontend изменения

#### Новые компоненты:
- `frontend/src/components/admin/OCRVersionToggle.js` - UI компонент переключателя
- `frontend/src/components/admin/index.js` - экспорт компонентов

#### Обновленные файлы:
- `frontend/src/components/SystemSettings.js` - интеграция OCRVersionToggle

### База данных

Версия OCR хранится в таблице `app_settings`:
- **Ключ:** `ocr_version`
- **Значения:** `v1.0` или `v2.0`
- **По умолчанию:** `v2.0`

```sql
-- Проверить текущую версию
SELECT * FROM app_settings WHERE key = 'ocr_version';

-- Изменить версию вручную (не рекомендуется)
UPDATE app_settings SET value = 'v1.0' WHERE key = 'ocr_version';
-- или
INSERT INTO app_settings (key, value) VALUES ('ocr_version', 'v1.0')
  ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
```

## 📊 Мониторинг

### Проверка используемой версии в логах

**Backend:**
```bash
docker logs bizcard-backend 2>&1 | grep "OCR v"
```

**Celery Worker:**
```bash
docker logs bizcard-celery-worker 2>&1 | grep "Using OCR"
```

Вы увидите:
- `🚀 Using OCR v2.0 for filename.jpg` - используется v2.0
- `🔧 Using OCR v1.0 for filename.jpg` - используется v1.0
- `⚠️ OCR v2.0 failed, falling back to v1.0` - автоматический fallback

### Мониторинг производительности

В админ-панели на вкладке **"Мониторинг"** (`/admin?tab=monitoring`) можно увидеть:
- Количество обработанных карточек
- Среднее время обработки
- Используемый OCR провайдер
- Статус валидации

## 🚀 Рекомендации

### Когда использовать v1.0:
- Нужна максимальная скорость обработки
- Визитки простого формата (только текст)
- Ограниченные ресурсы сервера

### Когда использовать v2.0:
- Нужна максимальная точность
- Сложные визитки с логотипами и графикой
- Необходима автоматическая классификация полей
- Важна автоматическая валидация данных
- Нужно сохранение в MinIO для ML обучения

## 🔄 Автоматический Fallback

При использовании v2.0:
1. Система пытается использовать PaddleOCR + LayoutLMv3
2. Если v2.0 не справляется - автоматически переключается на v1.0
3. Результат сохраняется с пометкой о методе распознавания
4. В логах фиксируется fallback

## 🎯 Примеры использования

### Быстрый batch-импорт (v1.0)
```python
import requests

# Переключаемся на v1.0 для скорости
requests.post(
    "https://ibbase.ru/api/ocr/settings/version",
    headers={"Authorization": f"Bearer {token}"},
    json={"version": "v1.0"}
)

# Загружаем много карточек
for file in files:
    upload_card(file)

# Возвращаемся на v2.0
requests.post(
    "https://ibbase.ru/api/ocr/settings/version",
    headers={"Authorization": f"Bearer {token}"},
    json={"version": "v2.0"}
)
```

### Проверка качества распознавания
```python
# Получаем информацию о последних сканированиях
response = requests.get(
    "https://ibbase.ru/api/monitoring/dashboard",
    headers={"Authorization": f"Bearer {token}"}
)

recent_scans = response.json()['recent_scans']

for scan in recent_scans:
    print(f"File: {scan['filename']}")
    print(f"Method: {scan['recognition_method']}")
    print(f"Confidence: {scan.get('confidence', 'N/A')}")
    print("---")
```

## 📝 Troubleshooting

### Версия не меняется

**Проблема:** После смены версии OCR продолжает использовать старую

**Решение:**
```bash
# Перезапустите celery-worker
cd /home/ubuntu/fastapi-bizcard-crm-ready
docker compose restart celery-worker

# Проверьте настройку в БД
docker exec -it bizcard-db psql -U bizcard -d bizcard_crm \
  -c "SELECT * FROM app_settings WHERE key = 'ocr_version';"
```

### OCR v2.0 постоянно падает

**Проблема:** v2.0 всегда fallback на v1.0

**Возможные причины:**
1. Недостаточно памяти для LayoutLMv3
2. Не установлены зависимости PaddleOCR
3. Проблемы с MinIO подключением

**Решение:**
```bash
# Проверьте логи
docker logs bizcard-celery-worker 2>&1 | grep -A 5 "OCR v2.0 failed"

# Проверьте ресурсы
docker stats bizcard-celery-worker

# Проверьте MinIO
curl http://localhost:9000/minio/health/ready
```

### Доступ запрещен (403)

**Проблема:** Не могу изменить версию OCR через API

**Причина:** Endpoint доступен только администраторам

**Решение:** Убедитесь, что ваш пользователь имеет роль `admin`

```bash
# Проверьте роль через API
curl -X GET "https://ibbase.ru/api/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📚 Связанные документы

- [OCR V2 Web Panels Guide](./OCR_V2_WEB_PANELS_GUIDE.md)
- [Quick Monitoring Reference](./QUICK_MONITORING_REFERENCE.md)
- [System Architecture](./SYSTEM_ARCHITECTURE.md)

## 🎉 Статус

✅ **Реализовано и протестировано**
- Backend API endpoints
- Frontend UI компонент
- Integration в SystemSettings
- Database хранение настроек
- Celery worker интеграция
- Automatic fallback механизм
- Мониторинг и логирование

---

**Дата создания:** 27 октября 2025  
**Версия системы:** v6.1.0  
**Автор:** AI Assistant (Claude Sonnet 4.5)

