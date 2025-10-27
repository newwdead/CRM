# 🌐 OCR v2.0 - Веб-Панели и Доступ

**Дата:** 27 октября 2025  
**Версия:** 6.0.0  
**Статус:** ✅ Работают, требуют настройки доступа

---

## 📦 Доступные Веб-Панели

### 1. 🗄️ MinIO Console (S3 Storage)

**Назначение:** Управление хранилищем изображений визиток и OCR результатов

**Статус:** ✅ Работает (healthy)

**Доступ (Локально на сервере):**
- **URL:** http://localhost:9001
- **API:** http://localhost:9000
- **Логин:** `admin`
- **Пароль:** `minio123456`

**Что можно делать:**
- 📂 Просматривать bucket'ы с изображениями
- 📊 Смотреть статистику хранилища
- 🔐 Управлять доступом и политиками
- 📁 Загружать/скачивать файлы
- 🔍 Просматривать метаданные файлов

**Bucket'ы (будут созданы автоматически):**
- `business-cards` - оригинальные изображения визиток
- `ocr-results` - результаты OCR распознавания
- `training-data` - данные для обучения моделей
- `models` - обученные модели

---

### 2. 🏷️ Label Studio (Annotation Tool)

**Назначение:** Визуальная аннотация визиток для обучения LayoutLMv3

**Статус:** ✅ Работает

**Доступ (Локально на сервере):**
- **URL:** http://localhost:8081
- **Логин:** `admin@ibbase.ru`
- **Пароль:** `_sAYqjD3qtrlx726a6lU1ZpfLdTmCfCE`

**Что можно делать:**
- 📝 Размечать поля на визитках (имя, компания, телефон, email...)
- 🖼️ Рисовать bounding box'ы вокруг текста
- 🤖 Обучать AI распознаванию полей
- 📊 Просматривать статистику аннотации
- 👥 Работать командой (несколько аннотаторов)

**Конфигурация разметки:**
Уже настроена для полей визитки:
- Full Name / Имя
- Company / Компания
- Position / Должность
- Phone / Телефон
- Email
- Website / Сайт
- Address / Адрес

---

## 🚀 Как Получить Доступ из Браузера

### ⚠️ Текущая Ситуация

Порты **слушают только на localhost** (127.0.0.1), поэтому недоступны напрямую из интернета.

```bash
# Текущие порты:
127.0.0.1:9000  → MinIO API
127.0.0.1:9001  → MinIO Console
127.0.0.1:8081  → Label Studio
```

### ✅ Способы Доступа

#### Вариант 1: SSH Туннель (Быстрый)

**Для MinIO Console:**
```bash
ssh -L 9001:localhost:9001 ubuntu@ibbase.ru
```

**Для Label Studio:**
```bash
ssh -L 8081:localhost:8081 ubuntu@ibbase.ru
```

Затем открыть в браузере:
- MinIO: http://localhost:9001
- Label Studio: http://localhost:8081

---

#### Вариант 2: Nginx Reverse Proxy (Рекомендуется)

Добавить в конфигурацию Nginx для доступа через домен.

**Для MinIO Console:**
```nginx
# /etc/nginx/sites-available/ibbase.ru

# MinIO Console
location /minio/ {
    proxy_pass http://localhost:9001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

**Для Label Studio:**
```nginx
# Label Studio
location /label-studio/ {
    proxy_pass http://localhost:8081/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Increase timeouts for large file uploads
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    client_max_body_size 100M;
}
```

После добавления:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

Доступ:
- MinIO: https://ibbase.ru/minio/
- Label Studio: https://ibbase.ru/label-studio/

---

## 📋 Инструкция по Настройке

### Шаг 1: Первый Вход в MinIO Console

1. SSH туннель или Nginx proxy
2. Открыть http://localhost:9001 (или https://ibbase.ru/minio/)
3. Войти:
   - **Access Key:** `admin`
   - **Secret Key:** `minio123456`

4. **Создать Bucket'ы:**
   - Нажать "Create Bucket +"
   - Создать: `business-cards`, `ocr-results`, `training-data`, `models`
   - Настроить Access Policy для каждого (например, Read-Only для business-cards)

5. **Создать Access Key для приложения:**
   - Identity → Service Accounts → Create Service Account
   - Сохранить Access Key и Secret Key
   - Обновить в `.env`:
     ```bash
     MINIO_ACCESS_KEY=новый_access_key
     MINIO_SECRET_KEY=новый_secret_key
     ```

---

### Шаг 2: Первый Вход в Label Studio

1. SSH туннель или Nginx proxy
2. Открыть http://localhost:8081 (или https://ibbase.ru/label-studio/)
3. Войти:
   - **Email:** `admin@ibbase.ru`
   - **Password:** `_sAYqjD3qtrlx726a6lU1ZpfLdTmCfCE`

4. **Создать Проект:**
   - "Create Project"
   - **Name:** "Business Cards OCR Training"
   - **Data Import:** Выбрать папку с изображениями (`/label-studio/files`)

5. **Настроить Labeling Config:**
   - Использовать конфигурацию из `backend/app/integrations/label_studio_config.xml`
   - Это уже готовая разметка для визиток

6. **Начать Аннотацию:**
   - Открыть первую визитку
   - Нарисовать box вокруг имени, выбрать "Full Name"
   - Нарисовать box вокруг компании, выбрать "Company"
   - И так далее...

---

## 🔐 Безопасность

### ⚠️ Важные Рекомендации

#### 1. Изменить Пароли

**MinIO:**
```bash
# В .env файле:
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=ВАША_СИЛЬНАЯ_ПАРОЛА_ТУТ
```

**Label Studio:**
```bash
# В .env файле:
LABEL_STUDIO_PASSWORD=ВАША_СИЛЬНАЯ_ПАРОЛА_ТУТ
```

После изменения:
```bash
docker compose down
docker compose up -d
```

#### 2. Ограничить Доступ по IP (Nginx)

```nginx
location /minio/ {
    allow 192.168.1.0/24;  # Ваша сеть
    deny all;
    
    proxy_pass http://localhost:9001/;
    # ... остальные настройки
}
```

#### 3. Использовать SSL (HTTPS)

Уже настроено для домена `ibbase.ru` через Let's Encrypt.

---

## 📊 Использование MinIO в Коде

Пример использования MinIO в приложении:

```python
from app.integrations.minio.client import MinIOClient
from app.services.storage_service import StorageService

# Инициализация
storage = StorageService()

# Сохранить изображение визитки
image_path = storage.save_business_card_image(
    image_data=file_bytes,
    contact_id=123,
    original_filename="card.jpg"
)

# Получить изображение
image_data = storage.get_business_card_image(contact_id=123)

# Сохранить OCR результат
storage.save_ocr_result(
    contact_id=123,
    ocr_data={"fields": {...}},
    raw_json=json_data
)
```

---

## 📊 Использование Label Studio для Обучения

### Workflow:

1. **Аннотация визиток** в Label Studio (вручную размечаете 100-200 визиток)
2. **Экспорт аннотаций** в JSON формате
3. **Подготовка датасета:**
   ```python
   from app.services.training.dataset_preparer import DatasetPreparer
   
   preparer = DatasetPreparer()
   dataset = preparer.prepare_from_label_studio(
       annotations_path="annotations.json",
       images_path="uploads/"
   )
   ```

4. **Обучение LayoutLMv3:**
   ```python
   from app.services.training.model_trainer import ModelTrainer
   
   trainer = ModelTrainer()
   trainer.train(
       train_dataset=dataset,
       output_dir="models/layoutlm-business-cards"
   )
   ```

5. **Использование обученной модели:**
   ```python
   # В backend/app/integrations/layoutlm/config.py
   fine_tuned_path = "models/layoutlm-business-cards"
   ```

---

## 🎯 Текущий Статус

| Сервис | Статус | Веб-Панель | Настройка |
|--------|--------|------------|-----------|
| **MinIO** | ✅ Работает | ✅ Есть (Console) | 🟡 Требует создания bucket'ов |
| **Label Studio** | ✅ Работает | ✅ Есть | 🟡 Требует создания проекта |
| **LayoutLMv3** | ✅ Установлен | ❌ Нет панели | ✅ Работает из коробки |
| **PaddleOCR** | ✅ Установлен | ❌ Нет панели | ✅ Работает из коробки |
| **Validator** | ✅ Установлен | ❌ Нет панели | ✅ Работает из коробки |

---

## 🚀 Быстрый Старт (5 минут)

### Для доступа через SSH туннель:

```bash
# 1. Создать туннели (на вашем локальном компьютере)
ssh -L 9001:localhost:9001 -L 8081:localhost:8081 ubuntu@ibbase.ru

# 2. Открыть в браузере:
# MinIO Console: http://localhost:9001
#   - Логин: admin
#   - Пароль: minio123456

# Label Studio: http://localhost:8081
#   - Email: admin@ibbase.ru
#   - Пароль: _sAYqjD3qtrlx726a6lU1ZpfLdTmCfCE

# 3. Создать bucket'ы в MinIO:
#   - business-cards
#   - ocr-results
#   - training-data
#   - models

# 4. Создать проект в Label Studio:
#   - Business Cards OCR Training
#   - Загрузить конфигурацию из label_studio_config.xml
```

---

## 📚 Полезные Ссылки

- **MinIO Docs:** https://docs.min.io/
- **Label Studio Docs:** https://labelstud.io/guide/
- **LayoutLMv3 Paper:** https://arxiv.org/abs/2204.08387
- **PaddleOCR GitHub:** https://github.com/PaddlePaddle/PaddleOCR

---

## ❓ FAQ

**Q: Нужно ли настраивать PaddleOCR и LayoutLMv3?**  
A: Нет, они работают из коробки. Модели скачаются автоматически при первом использовании.

**Q: Сколько визиток нужно разметить для обучения?**  
A: Минимум 100, оптимально 200-500 для хорошей точности.

**Q: Можно ли использовать MinIO без веб-панели?**  
A: Да, есть CLI (`mc`) и SDK для Python. Но веб-панель удобнее.

**Q: Как сбросить пароль Label Studio?**  
A: Изменить в `.env` файле `LABEL_STUDIO_PASSWORD` и пересоздать контейнер:
```bash
docker compose down label-studio
docker compose up -d label-studio
```

---

## 🎊 Готово!

Теперь у вас есть полноценная OCR v2.0 платформа с:
- ✅ S3-совместимым хранилищем (MinIO)
- ✅ Инструментом для аннотации (Label Studio)
- ✅ AI моделями (PaddleOCR + LayoutLMv3)
- ✅ Автоматической валидацией
- ✅ Веб-панелями для управления

**Следующий шаг:** Настроить Nginx proxy для удобного доступа через браузер!

