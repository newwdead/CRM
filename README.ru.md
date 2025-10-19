# 📇 BizCard CRM - Система управления визитными карточками

> **Полнофункциональная CRM система с OCR распознаванием визитных карточек и интеграцией с Telegram**

![Version](https://img.shields.io/badge/version-1.6-blue)
![Python](https://img.shields.io/badge/python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)
![React](https://img.shields.io/badge/React-18-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)

---

## 📋 Содержание

- [О проекте](#о-проекте)
- [Возможности](#возможности)
- [Технологический стек](#технологический-стек)
- [Структура проекта](#структура-проекта)
- [Быстрый старт](#быстрый-старт)
- [Настройка](#настройка)
- [Telegram интеграция](#telegram-интеграция)
- [SSL и HTTPS](#ssl-и-https)
- [API документация](#api-документация)
- [Разработка](#разработка)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## 🎯 О проекте

BizCard CRM - это современная веб-система для управления контактами, специализирующаяся на автоматическом распознавании визитных карточек. Система позволяет:

- 📸 **Загружать фотографии визиток** через веб-интерфейс или Telegram
- 🤖 **Автоматически распознавать текст** с помощью OCR (Tesseract или Parsio)
- 💼 **Управлять контактами** в удобном интерфейсе
- 📱 **Интегрироваться с Telegram** для мгновенной обработки визиток
- 📊 **Экспортировать данные** в CSV и XLSX форматы
- 🔍 **Искать и фильтровать** контакты

---

## ✨ Возможности

### 🖼️ OCR и распознавание
- **Два провайдера OCR:**
  - 🖥️ **Tesseract** (локальный, бесплатный) - поддержка русского и английского
  - ☁️ **Parsio** (облачный, платный) - высокая точность распознавания
- Многопроходная обработка изображений для лучшей точности
- Автоматическая нормализация и очистка данных
- Поддержка изображений до 20 МБ

### 📱 Telegram интеграция
- Автоматическая обработка фотографий из Telegram
- Два режима работы: **webhook** (production) и **polling** (development)
- Настройка разрешенных чатов
- Выбор провайдера OCR для Telegram сообщений
- Systemd сервис для автоматического запуска

### 💾 Управление контактами
- CRUD операции (создание, чтение, обновление, удаление)
- Массовые операции (bulk update/delete)
- Inline редактирование комментариев
- Просмотр привязанных фотографий
- Уникальные идентификаторы (UID) для каждого контакта

### 📊 Импорт/Экспорт
- Импорт из CSV и XLSX
- Экспорт в CSV и XLSX
- Экспорт выбранных контактов
- Автоматическая нормализация данных (NaN → null)

### 🎨 Современный интерфейс
- Адаптивный дизайн (мобильные устройства + десктоп)
- Многоязычность (русский + английский)
- Темная тема (опционально)
- Интуитивно понятный UX

---

## 🛠️ Технологический стек

### Backend
```
┌─────────────────────────────────────┐
│  FastAPI (веб-фреймворк)            │
│  ├─ Gunicorn + Uvicorn (ASGI)       │
│  ├─ SQLAlchemy (ORM)                │
│  ├─ PostgreSQL (БД)                 │
│  ├─ Pydantic (валидация)            │
│  └─ Tesseract OCR (распознавание)   │
└─────────────────────────────────────┘
```

**Ключевые библиотеки:**
- `fastapi` - веб-фреймворк
- `sqlalchemy` - ORM для работы с БД
- `pytesseract` - Python обертка для Tesseract
- `Pillow` - обработка изображений
- `pandas` - импорт/экспорт данных
- `openpyxl` - работа с Excel файлами
- `psycopg2-binary` - PostgreSQL драйвер

### Frontend
```
┌─────────────────────────────────────┐
│  React 18 (UI библиотека)           │
│  ├─ Create React App (сборка)       │
│  ├─ Axios (HTTP клиент)             │
│  └─ CSS Modules (стили)             │
└─────────────────────────────────────┘
```

### Infrastructure
```
┌─────────────────────────────────────┐
│  Docker + Docker Compose            │
│  ├─ Nginx (веб-сервер, прокси)      │
│  ├─ PostgreSQL 15 (БД)              │
│  └─ SSL/TLS (самоподписанный)       │
└─────────────────────────────────────┘
```

---

## 📁 Структура проекта

```
fastapi-bizcard-crm-ready/
│
├── 📂 backend/                      # Backend приложение (FastAPI)
│   ├── 📂 app/
│   │   ├── 📄 __init__.py          # Инициализация пакета
│   │   ├── 📄 main.py              # Основное приложение FastAPI
│   │   │                           # • CRUD endpoints для контактов
│   │   │                           # • Upload и OCR обработка
│   │   │                           # • Импорт/Экспорт CSV/XLSX
│   │   │                           # • Telegram webhook
│   │   │                           # • Health check и версия
│   │   │
│   │   ├── 📄 models.py            # SQLAlchemy модели
│   │   │                           # • Contact - модель контакта
│   │   │                           # • AppSetting - настройки приложения
│   │   │
│   │   ├── 📄 database.py          # Настройка БД
│   │   │                           # • Создание engine
│   │   │                           # • SessionLocal для сессий
│   │   │                           # • get_db() dependency
│   │   │
│   │   └── 📄 ocr_utils.py         # OCR функционал
│   │                               # • ocr_image_fileobj() - Tesseract
│   │                               # • ocr_parsio() - Parsio API
│   │                               # • parse_text() - парсинг результатов
│   │                               # • _normalize_contact() - нормализация
│   │
│   ├── 📄 requirements.txt         # Python зависимости
│   └── 📄 Dockerfile               # Docker образ для backend
│                                   # • Python 3.10-slim
│                                   # • Tesseract + русский язык
│                                   # • Gunicorn + Uvicorn
│
├── 📂 frontend/                     # Frontend приложение (React)
│   ├── 📂 src/
│   │   ├── 📂 components/
│   │   │   ├── 📄 ContactList.js   # Список контактов
│   │   │   │                       # • Поиск и фильтрация
│   │   │   │                       # • Inline редактирование
│   │   │   │                       # • Массовые операции
│   │   │   │
│   │   │   ├── 📄 ContactEdit.js   # Редактирование контакта
│   │   │   │                       # • Форма редактирования
│   │   │   │                       # • Превью фотографии
│   │   │   │
│   │   │   ├── 📄 UploadCard.js    # Загрузка визиток
│   │   │   │                       # • Выбор файла
│   │   │   │                       # • Выбор OCR провайдера
│   │   │   │                       # • Обработка и создание контакта
│   │   │   │
│   │   │   ├── 📄 ImportExport.js  # Импорт/Экспорт
│   │   │   │                       # • CSV импорт
│   │   │   │                       # • XLSX импорт/экспорт
│   │   │   │
│   │   │   ├── 📄 TelegramSettings.js # Настройки Telegram
│   │   │   │                       # • Включение/выключение
│   │   │   │                       # • Настройка токена
│   │   │   │                       # • Разрешенные чаты
│   │   │   │
│   │   │   └── 📄 LanguageToggle.js # Переключатель языка
│   │   │                           # • RU ⇄ EN
│   │   │
│   │   ├── 📄 App.js                # Главный компонент приложения
│   │   ├── 📄 App.css               # Глобальные стили
│   │   └── 📄 index.js              # Точка входа React
│   │
│   ├── 📂 public/                   # Статические файлы
│   ├── 📄 package.json              # NPM зависимости
│   ├── 📄 nginx.conf                # Конфигурация Nginx
│   │                                # • HTTP сервер (порт 80)
│   │                                # • HTTPS сервер (порт 8443)
│   │                                # • Проксирование /api/ → backend
│   │                                # • Проксирование /files/ → backend
│   │                                # • Telegram webhook endpoint
│   │
│   └── 📄 Dockerfile                # Docker образ для frontend
│                                    # • Multi-stage build
│                                    # • Node.js для сборки
│                                    # • Nginx для production
│
├── 📂 uploads/                      # Загруженные фотографии визиток
│                                    # (создается автоматически)
│
├── 📂 data/                         # Данные (если SQLite)
│                                    # (не используется в Docker режиме)
│
├── 📄 docker-compose.yml            # Docker Compose конфигурация
│                                    # • db - PostgreSQL 15
│                                    # • backend - FastAPI приложение
│                                    # • frontend - React + Nginx
│
├── 📄 docker-compose.prod.yml       # Production оверлей
│                                    # • Скрытие портов backend
│                                    # • Volumes для данных
│                                    # • Переменные окружения
│
├── 📄 telegram_polling.py           # Скрипт для Telegram polling
│                                    # • Получение обновлений от Telegram
│                                    # • Отправка в локальный webhook
│                                    # • Автоматическая обработка
│
├── 📄 telegram-polling.service      # Systemd сервис для polling
│                                    # • Автозапуск при старте системы
│                                    # • Автоматический рестарт
│
├── 📄 .env.example                  # Шаблон переменных окружения
│                                    # • DATABASE_URL
│                                    # • PARSIO_API_KEY
│                                    # • TELEGRAM_TOKEN
│
├── 📄 README.md                     # Документация (English)
├── 📄 README.ru.md                  # Документация (Русский) ← ВЫ ЗДЕСЬ
├── 📄 SSL_SETUP.md                  # Инструкция по SSL
├── 📄 TELEGRAM_SETUP.md             # Инструкция по Telegram
│
└── 📄 RELEASE_NOTES_v1.*.md         # История релизов
```

---

## 🚀 Быстрый старт

### Предварительные требования

- Docker (v20.10+)
- Docker Compose (v2.0+)
- 4 ГБ свободной оперативной памяти
- 10 ГБ свободного места на диске

### Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/yourusername/fastapi-bizcard-crm.git
cd fastapi-bizcard-crm-ready

# 2. (Опционально) Создать файл .env
cp .env.example .env
# Отредактируйте .env если нужно

# 3. Собрать и запустить контейнеры
docker compose up -d --build

# 4. Дождаться запуска (30-60 секунд)
docker compose logs -f

# 5. Открыть в браузере
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
# HTTPS:     https://localhost:8443
```

### Проверка работоспособности

```bash
# Проверить статус контейнеров
docker compose ps

# Проверить health endpoint
curl http://localhost:8000/health

# Посмотреть логи
docker compose logs backend
docker compose logs frontend
docker compose logs db
```

---

## ⚙️ Настройка

### Переменные окружения

Создайте файл `.env` в корне проекта:

```ini
# ============================================
# База данных
# ============================================
DATABASE_URL=postgresql://postgres:password@db:5432/bizcard_crm
POSTGRES_DB=bizcard_crm
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here

# ============================================
# Parsio Cloud OCR (опционально)
# ============================================
PARSIO_API_KEY=your_parsio_api_key
PARSIO_API_URL=https://api.parsio.io/mailboxes/<mailbox_id>/upload
PARSIO_DOCUMENT_URL_TEMPLATE=https://api.parsio.io/docs/{id}
PARSIO_AUTH_HEADER_NAME=X-API-Key
PARSIO_AUTH_HEADER_VALUE={key}
PARSIO_TIMEOUT=45
PARSIO_POLL_INTERVAL=2.0
PARSIO_POLL_MAX_ATTEMPTS=20

# ============================================
# Приложение
# ============================================
APP_VERSION=v1.6
APP_COMMIT=
APP_MESSAGE=Production deployment
TZ=Europe/Moscow
```

### Настройка Telegram

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен (например: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
3. Настройте через Web UI или API:

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

4. Запустите polling сервис:

```bash
# Скопировать токен в сервис
sudo nano /etc/systemd/system/telegram-polling.service

# Запустить сервис
sudo systemctl enable telegram-polling
sudo systemctl start telegram-polling

# Проверить статус
sudo systemctl status telegram-polling
```

Подробнее см. [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)

---

## 📱 Telegram интеграция

### Как это работает

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   Telegram  │──1──>│   Polling    │──2──>│   Backend   │
│     Bot     │       │    Script    │       │  /webhook   │
└─────────────┘       └──────────────┘       └─────────────┘
                              │                      │
                              │                      ▼
                              │              ┌─────────────┐
                              └────3────────│  Tesseract  │
                                             │     OCR     │
                                             └─────────────┘
                                                    │
                                                    ▼
                                             ┌─────────────┐
                                             │ PostgreSQL  │
                                             │  Database   │
                                             └─────────────┘
```

**Процесс:**
1. Пользователь отправляет фото в Telegram бота
2. Polling скрипт получает обновление (каждую секунду)
3. Фото скачивается и отправляется на `/telegram/webhook`
4. Backend обрабатывает фото через OCR (Tesseract или Parsio)
5. Распознанные данные сохраняются в базу как новый контакт

### Режимы работы

#### 🔄 Polling (рекомендуется для dev)

**Преимущества:**
- ✅ Работает везде (не нужен публичный IP)
- ✅ Простая настройка
- ✅ Не требует SSL

**Запуск:**
```bash
sudo systemctl start telegram-polling
sudo journalctl -u telegram-polling -f
```

#### 🌐 Webhook (рекомендуется для production)

**Преимущества:**
- ✅ Мгновенная доставка
- ✅ Меньше нагрузки

**Требования:**
- Публичный IP или домен
- SSL сертификат
- Открытый порт 8443 или 443

**Настройка:**
```bash
TELEGRAM_TOKEN="ваш_токен"
curl -F "url=https://yourdomain.com:8443/telegram/webhook" \
     -F "certificate=@/etc/nginx/certs/selfsigned.crt" \
     "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook"
```

---

## 🔒 SSL и HTTPS

Проект поддерживает HTTPS для Telegram webhook и безопасного доступа.

### Самоподписанный сертификат (development)

```bash
# Создать директорию
sudo mkdir -p /etc/nginx/certs

# Сгенерировать сертификат
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/nginx/certs/selfsigned.key \
  -out /etc/nginx/certs/selfsigned.crt \
  -days 365 \
  -subj "/CN=localhost/O=BizCard CRM/C=RU"

# Перезапустить frontend
docker compose restart frontend
```

### Let's Encrypt (production)

```bash
# Установить certbot
sudo apt install certbot

# Получить сертификат
sudo certbot certonly --standalone -d yourdomain.com

# Обновить docker-compose.yml
# volumes:
#   - /etc/letsencrypt/live/yourdomain.com:/etc/nginx/certs:ro
```

Подробнее см. [SSL_SETUP.md](SSL_SETUP.md)

---

## 📖 API документация

### Автоматическая документация

FastAPI автоматически генерирует интерактивную документацию:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Основные endpoints

#### Контакты

```http
# Получить все контакты
GET /contacts/

# Получить контакт по ID
GET /contacts/{id}

# Получить контакт по UID
GET /contacts/uid/{uid}

# Создать контакт
POST /contacts/
Content-Type: application/json
{
  "full_name": "Иван Иванов",
  "company": "ООО Компания",
  "position": "Директор",
  "email": "ivan@company.ru",
  "phone": "+7 (123) 456-78-90",
  "address": "Москва, ул. Пушкина",
  "comment": "Важный клиент",
  "website": "https://company.ru"
}

# Обновить контакт
PUT /contacts/{id}
Content-Type: application/json
{ ... }

# Удалить контакт
DELETE /contacts/{id}

# Массовое удаление
POST /contacts/delete_bulk
Content-Type: application/json
[1, 2, 3, 4]

# Массовое обновление
PUT /contacts/update_bulk
Content-Type: application/json
{
  "ids": [1, 2, 3],
  "fields": {
    "comment": "Обновленный комментарий"
  }
}
```

#### Загрузка и OCR

```http
# Загрузить и распознать визитку
POST /upload/?provider=tesseract
Content-Type: multipart/form-data
file: <binary>

# Провайдеры: tesseract | parsio
```

#### Импорт/Экспорт

```http
# Экспорт в CSV
GET /contacts/export
GET /contacts/export?ids=1,2,3

# Экспорт в XLSX
GET /contacts/export/xlsx
GET /contacts/export/xlsx?ids=1,2,3

# Импорт из CSV/XLSX
POST /contacts/import
Content-Type: multipart/form-data
file: <binary>
```

#### Telegram

```http
# Получить настройки
GET /settings/telegram

# Обновить настройки
PUT /settings/telegram
Content-Type: application/json
{
  "enabled": true,
  "token": "bot_token",
  "allowed_chats": "123,456",
  "provider": "tesseract"
}

# Webhook endpoint (для Telegram API)
POST /telegram/webhook
Content-Type: application/json
{ ... telegram update ... }
```

#### Система

```http
# Health check
GET /health
→ {"status": "ok"}

# Версия приложения
GET /version
→ {
  "version": "v1.6",
  "commit": "abc123",
  "message": "Production"
}
```

---

## 🔧 Разработка

### Локальный запуск (без Docker)

#### Backend

```bash
cd backend

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Установить Tesseract
# Ubuntu/Debian:
sudo apt install tesseract-ocr tesseract-ocr-rus

# MacOS:
brew install tesseract tesseract-lang

# Настроить БД
export DATABASE_URL="postgresql://user:pass@localhost/bizcard_crm"

# Запустить сервер
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev сервер
npm start

# Открыть http://localhost:3000
```

### Структура базы данных

```sql
-- Таблица контактов
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    uid VARCHAR UNIQUE,                  -- Уникальный идентификатор
    full_name VARCHAR,                   -- ФИО
    company VARCHAR,                     -- Название компании
    position VARCHAR,                    -- Должность
    email VARCHAR,                       -- Email
    phone VARCHAR,                       -- Телефон
    address VARCHAR,                     -- Адрес
    comment VARCHAR,                     -- Комментарий
    website VARCHAR,                     -- Веб-сайт
    photo_path VARCHAR,                  -- Путь к фото визитки
    ocr_raw VARCHAR                      -- Сырые данные OCR (JSON)
);

-- Таблица настроек
CREATE TABLE app_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR UNIQUE NOT NULL,         -- Ключ настройки
    value VARCHAR                        -- Значение настройки
);

-- Примеры настроек:
-- tg.enabled = 'true'|'false'
-- tg.token = 'bot_token'
-- tg.allowed_chats = '123,456'
-- tg.provider = 'tesseract'|'parsio'
```

### Добавление новых полей

1. Обновить модель в `backend/app/models.py`:
```python
class Contact(Base):
    # ...
    new_field = Column(String, nullable=True)
```

2. Добавить миграцию в `backend/app/main.py`:
```python
conn.execute(text("""
    ALTER TABLE contacts ADD COLUMN IF NOT EXISTS new_field VARCHAR;
"""))
```

3. Обновить Pydantic схемы:
```python
class ContactCreate(BaseModel):
    # ...
    new_field: Optional[str] = None
```

4. Обновить frontend компоненты

---

## 🚢 Deployment

### Docker Compose (рекомендуется)

```bash
# Production режим
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Проверка
docker compose ps
docker compose logs -f
```

### Переменные окружения для production

```ini
# Backend
TZ=Europe/Moscow
DATABASE_URL=postgresql://postgres:secure_password@db:5432/bizcard_crm
APP_VERSION=v1.6
APP_MESSAGE=Production deployment

# Parsio (опционально)
PARSIO_API_KEY=your_key
PARSIO_API_URL=https://api.parsio.io/mailboxes/xxx/upload

# PostgreSQL
POSTGRES_PASSWORD=very_secure_password_here
```

### Backup и восстановление

```bash
# Бэкап базы данных
docker compose exec db pg_dump -U postgres bizcard_crm > backup_$(date +%Y%m%d).sql

# Восстановление
docker compose exec -T db psql -U postgres bizcard_crm < backup_20250101.sql

# Бэкап загруженных файлов
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

### Мониторинг

```bash
# Логи в реальном времени
docker compose logs -f --tail 100

# Использование ресурсов
docker stats

# Проверка health
curl http://localhost:8000/health
```

---

## 🐛 Troubleshooting

### Контейнеры не запускаются

```bash
# Проверить логи
docker compose logs

# Пересоздать контейнеры
docker compose down -v
docker compose up -d --build
```

### Ошибка подключения к БД

```bash
# Проверить статус PostgreSQL
docker compose exec db psql -U postgres -c "SELECT version();"

# Проверить переменные окружения
docker compose exec backend env | grep DATABASE_URL
```

### Tesseract не распознает русский текст

```bash
# Проверить установленные языки
docker compose exec backend tesseract --list-langs

# Должны быть: eng, rus

# Пересобрать образ
docker compose build backend
```

### Telegram не получает сообщения

```bash
# Проверить polling сервис
sudo systemctl status telegram-polling
sudo journalctl -u telegram-polling -f

# Проверить настройки
curl http://localhost:8000/settings/telegram

# Проверить webhook в Telegram
TELEGRAM_TOKEN="your_token"
curl "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getWebhookInfo"
```

### Frontend показывает ошибку CORS

```bash
# Проверить настройки CORS в backend/app/main.py
# Добавить ваш домен в allow_origins

# Перезапустить backend
docker compose restart backend
```

---

## 📝 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

## 👥 Контакты и поддержка

- 📧 Email: support@example.com
- 💬 Telegram: @yourusername
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/fastapi-bizcard-crm/issues)

---

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) - отличный Python веб-фреймворк
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - мощный OCR движок
- [React](https://react.dev/) - библиотека для UI
- [PostgreSQL](https://www.postgresql.org/) - надежная СУБД

---

**Сделано с ❤️ для автоматизации работы с визитными карточками**

