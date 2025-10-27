# ✅ MinIO Setup Complete

**Date:** October 27, 2025  
**Version:** 6.0.0 (OCR v2.0)  
**URL:** https://ibbase.ru/minio/

---

## 🎯 Status: WORKING ✅

MinIO Console успешно работает через reverse proxy!

### 🔐 Доступ
- **URL:** https://ibbase.ru/minio/
- **Username:** `admin`
- **Password:** `minio123456`

---

## 📦 Созданные бакеты для OCR v2.0

| Бакет | Назначение | Политика доступа |
|-------|------------|------------------|
| `business-cards` | 📸 Изображения визиток | Public Download |
| `ocr-results` | 📝 Результаты OCR обработки | Private |
| `training-data` | 🎓 Данные для обучения моделей | Private |
| `models` | 🤖 Сохраненные ML модели | Private |

---

## ✅ Проверка работы

```bash
# Список бакетов
$ docker exec bizcard-minio mc ls local/
[2025-10-27 07:16:39 UTC]     0B business-cards/     ✅
[2025-10-27 07:16:45 UTC]     0B models/             ✅
[2025-10-27 07:16:45 UTC]     0B ocr-results/        ✅
[2025-10-27 07:16:45 UTC]     0B training-data/      ✅
```

---

## 🔧 Интеграция с Backend

MinIO готов к использованию в OCR v2.0 системе!

### Переменные окружения
В `.env` файле используются:
```bash
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=minio123456
```

### Python клиент
Backend использует `MinIOClient` из `backend/app/integrations/minio/client.py`:

```python
from app.integrations.minio import MinIOClient, BUCKET_NAMES

# Создание клиента
minio_client = MinIOClient()

# Использование бакетов
minio_client.save_image(
    bucket_name=BUCKET_NAMES['images'],  # 'business-cards'
    object_name='card_123.jpg',
    data=image_bytes
)
```

---

## 📊 Использование MinIO Console

### 1. Вход в систему
- Откройте https://ibbase.ru/minio/
- Введите: `admin` / `minio123456`

### 2. Просмотр бакетов
- В левом меню выберите "Buckets"
- Вы увидите все 4 бакета

### 3. Загрузка файлов
- Кликните на бакет (например, `business-cards`)
- Нажмите "Upload" → "Upload File"
- Выберите файл изображения

### 4. Просмотр файлов
- Кликните на имя файла для просмотра
- Используйте "Preview" для предпросмотра изображений

### 5. Управление доступом
- Settings → Access Policy
- Можно настроить публичный/приватный доступ

---

## 🔄 Workflow OCR v2.0 с MinIO

```
1. Загрузка визитки через Frontend
   ↓
2. Backend сохраняет изображение в MinIO
   → Бакет: business-cards
   → Путь: /card_{id}_{timestamp}.jpg
   ↓
3. OCR обработка (PaddleOCR + LayoutLMv3)
   ↓
4. Результаты сохраняются в MinIO
   → Бакет: ocr-results
   → Путь: /result_{card_id}.json
   ↓
5. Аннотация в Label Studio (опционально)
   ↓
6. Обучение моделей
   → Бакет: training-data (датасеты)
   → Бакет: models (обученные модели)
```

---

## 🎨 MinIO Console Features

### Доступные возможности:
- ✅ Просмотр и управление бакетами
- ✅ Загрузка и скачивание файлов
- ✅ Предпросмотр изображений
- ✅ Управление политиками доступа
- ✅ Версионирование файлов
- ✅ Метаданные объектов
- ✅ Поиск по файлам
- ✅ Статистика использования

### Monitoring:
- Dashboard → Object Browser
- Посмотреть размер хранилища
- Количество объектов
- Историю операций

---

## 🛠️ Полезные команды

### Через Docker (внутри контейнера)
```bash
# Список бакетов
docker exec bizcard-minio mc ls local/

# Список файлов в бакете
docker exec bizcard-minio mc ls local/business-cards/

# Загрузить файл
docker exec bizcard-minio mc cp /path/to/file.jpg local/business-cards/

# Скачать файл
docker exec bizcard-minio mc cp local/business-cards/file.jpg /tmp/

# Удалить файл
docker exec bizcard-minio mc rm local/business-cards/file.jpg

# Статистика бакета
docker exec bizcard-minio mc du local/business-cards/
```

### Через Python Backend
```python
from app.services.storage_service import StorageService

storage = StorageService()

# Сохранить изображение визитки
storage.save_card_image(
    card_id=123,
    image_data=image_bytes,
    filename='card.jpg'
)

# Получить изображение
image_url = storage.get_card_image_url(card_id=123)

# Сохранить OCR результат
storage.save_ocr_result(
    card_id=123,
    result_data=ocr_json
)

# Получить OCR результат
ocr_data = storage.get_ocr_result(card_id=123)
```

---

## 🔐 Безопасность

### Текущая конфигурация:
- ✅ MinIO работает на localhost (127.0.0.1)
- ✅ Доступ только через Nginx reverse proxy
- ✅ HTTPS соединение
- ✅ Авторизация по логину/паролю
- ⚠️ Пароль в `.env` файле (рекомендуется использовать Docker secrets)

### Рекомендации:
1. **Сменить пароль по умолчанию:**
   ```bash
   # В .env файле измените:
   MINIO_ROOT_PASSWORD=your_strong_password_here
   # Затем пересоздайте контейнер:
   docker compose up -d minio
   ```

2. **Создать Access Keys для приложений:**
   - MinIO Console → Identity → Service Accounts
   - Создайте отдельный Access Key для backend
   - Используйте его вместо root credentials

3. **Настроить lifecycle политики:**
   - Автоматическое удаление старых файлов
   - Переход в архивное хранилище

---

## 📈 Мониторинг

### Через MinIO Console:
- Dashboard → Metrics
- Просмотр использования диска
- Количество запросов
- Скорость передачи данных

### Через Prometheus (если настроен):
MinIO предоставляет метрики на `/minio/v2/metrics/cluster`

---

## 🎉 Итого

| Компонент | Статус | URL |
|-----------|--------|-----|
| MinIO API | ✅ Running | http://localhost:9000 |
| MinIO Console | ✅ Running | https://ibbase.ru/minio/ |
| Бакеты | ✅ Created | 4 бакета |
| Backend Integration | ✅ Ready | MinIOClient |

**Система готова к использованию в OCR v2.0!** 🚀

---

## 📝 Следующие шаги

1. ✅ MinIO настроен и работает
2. ⏳ **Проверить Label Studio:** https://ibbase.ru/label-studio/
3. ⏳ Протестировать загрузку визитки через UI
4. ⏳ Проверить сохранение изображений в MinIO
5. ⏳ Проверить OCR обработку с сохранением результатов

**Готово к тестированию полного workflow!** 🎊


