# 📚 FastAPI Business Card CRM - Project Knowledge Summary

**Generated:** 21 октября 2025  
**Current Version:** v2.15.1 (Hotfix)  
**Status:** Production Ready ✅

---

## 📋 Оглавление

1. [Общий обзор проекта](#общий-обзор-проекта)
2. [Архитектура системы](#архитектура-системы)
3. [Структура кодовой базы](#структура-кодовой-базы)
4. [Ключевые компоненты](#ключевые-компоненты)
5. [Технологический стек](#технологический-стек)
6. [Текущее состояние](#текущее-состояние)
7. [Технический долг](#технический-долг)
8. [CI/CD и DevOps](#cicd-и-devops)
9. [Рекомендации для разработки](#рекомендации-для-разработки)

---

## 🎯 Общий обзор проекта

### Назначение
**BizCard CRM** - полнофункциональная CRM-система для управления визитными карточками с автоматическим OCR-распознаванием, интеграциями с мессенджерами и продвинутыми возможностями поиска дубликатов.

### Ключевые возможности

| Категория | Функционал |
|-----------|-----------|
| **OCR Processing** | Tesseract (local), Google Vision (cloud), PaddleOCR (advanced) |
| **Contact Management** | CRUD, bulk operations, tags, groups, comments |
| **Integrations** | Telegram Bot (webhook/polling), WhatsApp Business API |
| **Duplicate Detection** | Fuzzy matching, configurable thresholds, merge UI |
| **Import/Export** | CSV, XLSX with drag & drop |
| **Authentication** | JWT tokens, role-based access (Admin/User) |
| **Monitoring** | Prometheus metrics, Grafana dashboards |
| **Admin Panel** | User management, settings, documentation viewer |

### Статистика кодовой базы

```
Backend:  49 Python файлов (~6,874 строк в ключевых файлах)
Frontend: 36 JavaScript файлов (React 18)
Tests:    Pytest с fixtures (conftest.py)
Docs:     52 markdown файла (release notes, guides)
```

---

## 🏗️ Архитектура системы

### Контейнерная архитектура (Docker Compose)

```
┌─────────────────────────────────────────────────────┐
│              Docker Compose Stack                   │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Frontend │  │ Backend  │  │  Celery  │        │
│  │ (React)  │  │(FastAPI) │  │  Worker  │        │
│  │  :3000   │  │  :8000   │  │          │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │              │               │
│  ┌────▼─────────────▼──────────────▼────┐         │
│  │                                       │         │
│  │  ┌──────────┐  ┌───────┐  ┌────────┐│         │
│  │  │PostgreSQL│  │ Redis │  │ Label  ││         │
│  │  │   :5432  │  │ :6379 │  │Studio  ││         │
│  │  └──────────┘  └───────┘  └────────┘│         │
│  │                                       │         │
│  │  Monitoring Stack:                    │         │
│  │  - Prometheus :9090                   │         │
│  │  - Grafana :3001                      │         │
│  │  - cAdvisor :8080                     │         │
│  │  - Node Exporter :9100                │         │
│  │  - Postgres Exporter :9187            │         │
│  └───────────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

### Текущий статус сервисов (Docker)

| Service | Status | Port | Health |
|---------|--------|------|--------|
| **backend** | ✅ Up 2h | 8000 | - |
| **frontend** | ✅ Up 4h | 3000 | - |
| **db (postgres)** | ✅ Up 25h | 5432 | - |
| **redis** | ✅ Up 25h | 6379 | ✅ Healthy |
| **celery-worker** | ✅ Up 4h | - | - |
| **prometheus** | ✅ Up 28h | 9090 | - |
| **grafana** | ✅ Up 28h | 3001 | - |
| **cadvisor** | ✅ Up 28h | 8080 | ✅ Healthy |
| **label-studio** | ✅ Up 23h | 8081 | - |

---

## 📂 Структура кодовой базы

### Backend Structure (Modular Architecture)

```
backend/app/
├── api/                    # API Routes (REST endpoints)
│   ├── admin.py           # Admin panel endpoints
│   ├── auth.py            # Authentication & registration
│   ├── contacts.py        # Contact CRUD operations ⚠️ 419 lines
│   ├── duplicates.py      # Duplicate detection
│   ├── ocr.py             # OCR processing endpoints
│   └── settings.py        # System settings
│
├── models/                 # SQLAlchemy ORM Models
│   ├── user.py            # User & authentication
│   ├── contact.py         # Contact entity
│   ├── duplicate.py       # Duplicate pairs
│   ├── ocr.py             # OCR results
│   ├── settings.py        # System settings
│   ├── audit.py           # Audit logs
│   └── base.py            # Base model classes
│
├── schemas/                # Pydantic Schemas
│   ├── (similar structure to models)
│   └── validation, serialization
│
├── services/               # Business Logic Layer
│   ├── contact_service.py  # Contact operations
│   ├── ocr_service.py      # OCR processing
│   ├── duplicate_service.py # Duplicate detection
│   └── settings_service.py  # Settings management
│
├── core/                   # Core Utilities
│   └── (shared utilities)
│
├── tests/                  # Pytest Tests
│   ├── conftest.py         # Test fixtures ⚠️ Recently fixed
│   └── test_*.py
│
├── main.py                 # FastAPI Application Entry ⚠️ 4072 lines!
├── database.py             # Database connection
├── auth_utils.py           # JWT, password hashing
├── ocr_providers.py        # OCR provider implementations
├── ocr_utils.py            # OCR utilities ✅ Fixed in v2.15.1
├── image_processing.py     # Image preprocessing
├── qr_utils.py             # QR code detection
├── duplicate_utils.py      # Fuzzy matching logic
├── phone_utils.py          # Phone number parsing
├── whatsapp_utils.py       # WhatsApp integration
├── tasks.py                # Celery tasks
└── celery_app.py           # Celery configuration
```

### Frontend Structure (React 18)

```
frontend/src/
├── components/
│   ├── AdminPanel.js       ⚠️ 1372 lines (needs splitting)
│   ├── ContactList.js      ⚠️ 1008 lines (needs splitting)
│   ├── ContactCard.js
│   ├── ContactEdit.js
│   ├── OCREditor.js        # OCR result editor
│   ├── OCREditorWithBlocks.js
│   ├── DuplicateFinder.js
│   ├── DuplicateMergeModal.js
│   ├── ImportExport.js
│   ├── Login.js / Register.js
│   ├── Settings.js
│   ├── SystemSettings.js
│   ├── TelegramSettings.js
│   ├── ServiceManager.js   # Docker service control
│   ├── Documentation.js    # Markdown viewer
│   └── pages/
│       └── (page components)
│
├── App.js                  # Main app component
├── index.js                # Entry point
├── translations.js         # i18n strings
└── index.css               # Global styles (Tailwind)
```

---

## 🔑 Ключевые компоненты

### Backend

#### 1. **main.py** (FastAPI Application)
- **Роль:** Главный файл приложения
- **Проблема:** 4072 строки - монолитный файл ⚠️
- **Содержит:**
  - FastAPI app initialization
  - CORS middleware
  - Rate limiting (slowapi)
  - Prometheus metrics
  - All route includes
  - Legacy endpoints (постепенно переносятся в `api/`)

#### 2. **api/** (Modular Routes)
- **auth.py** - JWT login, registration, token refresh
- **contacts.py** - CRUD для контактов (419 строк)
- **admin.py** - User management, admin-only endpoints
- **ocr.py** - Upload & OCR processing
- **duplicates.py** - Duplicate detection & merging
- **settings.py** - System configuration

#### 3. **services/** (Business Logic)
- Service Layer Architecture (NEW in v2.15)
- Отделяет бизнес-логику от API routes
- Пример: `contact_service.py` - CRUD operations
- Планируется расширение

#### 4. **OCR System**
```python
OCRManager (ocr_providers.py)
├── TesseractProvider (local, free)
├── GoogleVisionProvider (cloud, paid)
└── PaddleOCRProvider (advanced, local)

OCR Utils (ocr_utils.py) ✅ Fixed v2.15.1
├── parse_russian_name()
├── detect_company_and_position()
├── parse_phone_numbers()
└── extract_addresses()
```

#### 5. **Duplicate Detection**
- Fuzzy matching algorithms
- Configurable thresholds (name, phone, email)
- Merge UI with field-by-field selection

#### 6. **Celery Tasks**
- Асинхронная обработка OCR
- Background задачи
- Redis как broker

### Frontend

#### 1. **AdminPanel.js** (1372 lines) ⚠️
- User management table
- Settings tabs (General, OCR, Telegram, System)
- Documentation viewer
- Service manager
- **Требует разбиения на подкомпоненты**

#### 2. **ContactList.js** (1008 lines) ⚠️
- Contact table with filtering
- Bulk operations (select, delete, update)
- Inline editing
- Export functionality
- **Требует разбиения на подкомпоненты**

#### 3. **OCREditor.js**
- Редактирование результатов OCR
- Preview изображения
- Field-by-field editing
- Save to contacts

#### 4. **DuplicateFinder.js**
- Search for duplicates
- Threshold configuration
- Merge modal integration

---

## 🛠️ Технологический стек

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | latest | REST API framework |
| **ORM** | SQLAlchemy | 2.x | Database ORM |
| **Database** | PostgreSQL | 15 | Primary data store |
| **Cache** | Redis | 7 | Celery broker, caching |
| **Task Queue** | Celery | 5.x | Async processing |
| **Auth** | JWT | - | Token-based auth |
| **OCR** | Tesseract | 5.x | Local OCR |
| **OCR** | Google Vision | - | Cloud OCR (optional) |
| **OCR** | PaddleOCR | - | Advanced OCR (optional) |
| **Testing** | Pytest | - | Unit & integration tests |
| **Monitoring** | Prometheus | latest | Metrics collection |
| **Monitoring** | Grafana | latest | Dashboards |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18.2.0 | UI framework |
| **Routing** | React Router | 6.20.0 | SPA routing |
| **Styling** | Tailwind CSS | - | Utility-first CSS |
| **UI** | Framer Motion | 10.16.16 | Animations |
| **File Upload** | React Dropzone | 14.2.3 | Drag & drop |
| **Notifications** | React Hot Toast | 2.4.1 | Toast notifications |
| **Markdown** | React Markdown | 9.0.1 | Docs rendering |
| **Build** | Create React App | 5.0.1 | Build tooling |

### DevOps Stack

| Tool | Purpose | Status |
|------|---------|--------|
| **Docker** | Containerization | ✅ Active |
| **Docker Compose** | Multi-container orchestration | ✅ Active |
| **GitHub Actions** | CI/CD | ✅ Active |
| **Nginx** | Reverse proxy | ✅ Active |
| **Prometheus** | Metrics | ✅ Running |
| **Grafana** | Visualization | ✅ Running |
| **cAdvisor** | Container monitoring | ✅ Running |

---

## 📊 Текущее состояние

### Версии

- **Current:** v2.15.1 (Hotfix) - 21 октября 2025
- **Previous:** v2.15 - Service Layer Architecture
- **Release Cycle:** Regular updates, ~15 releases

### Последние изменения (v2.15.1)

✅ **Исправлено 3 CI ошибки:**
1. Отступы в `ocr_utils.py` (строки 254, 314)
2. Удалён `frontend/package-lock.json` из `.gitignore`
3. Добавлен `--legacy-peer-deps` в CI workflow

### GitHub Actions Status

**Workflows:**
- ✅ **CI** - Backend tests, frontend build, Docker builds
- ✅ **Security Scan** - Trivy, Safety, NPM audit
- ✅ **Release** - Automatic releases on tags

**Последний запуск:** 21 октября 2025
- CI Workflow: ✅ Запущен
- Release Workflow: ✅ Запущен (v2.15.1)

---

## ⚠️ Технический долг

### 🔴 Высокий приоритет

#### 1. Монолитный `main.py` (4072 строки)
**Статус:** 🟡 В процессе  
**Проблема:**
- Смешивание routing, бизнес-логики, конфигурации
- Сложно поддерживать и тестировать

**План:**
- [x] Разделены models → 7 модулей
- [x] Разделены schemas → 6 модулей
- [x] Созданы модульные API routes (`api/`)
- [ ] Переместить оставшиеся endpoints
- [ ] Создать полноценный service layer
- [ ] Уменьшить `main.py` до < 500 строк

#### 2. Большие React компоненты
**Статус:** 🔴 Не начато  
**Проблемы:**
- `AdminPanel.js` - 1372 строки
- `ContactList.js` - 1008 строк

**Решение:**
```
AdminPanel/ → UsersTab, SettingsTab, DocsTab, etc.
ContactList/ → ContactTable, ContactFilters, ContactActions
```

**Estimate:** 8-12 часов

#### 3. Дублирование Prometheus метрик
**Статус:** 🟡 Частично исправлено  
**Проблема:**
- Метрики определены в нескольких местах
- Вызывает `ValueError: Duplicated timeseries`

**Решение:**
- Создать централизованный `core/metrics.py`
- Импортировать из единого источника

### 🟡 Средний приоритет

#### 4. Отсутствие полноценного Service Layer
**Статус:** 🟡 Частично реализован (v2.15)  
**Проблема:**
- Бизнес-логика смешана с API routes
- Сложно тестировать

**Решение:**
- Расширить `services/` для всех entities
- Переместить логику из `api/` в `services/`

#### 5. Тестовое покрытие
**Статус:** 🟡 Частичное покрытие  
**Проблемы:**
- Недостаточно unit тестов
- Нет интеграционных тестов для всех API

**План:**
- Увеличить покрытие до 70%+
- Добавить E2E тесты

#### 6. Отсутствие `package-lock.json`
**Статус:** ✅ Исправлено в v2.15.1  
**Было:** Файл в `.gitignore`  
**Стало:** Удалено из `.gitignore`, может быть добавлен

---

## 🚀 CI/CD и DevOps

### GitHub Actions Workflows

#### 1. **CI Workflow** (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main`
- Pull requests
- Manual dispatch

**Jobs:**
```yaml
backend:
  - Setup Python 3.10
  - Install dependencies (requirements.txt)
  - Run flake8 linting
  - Run black formatting check
  - Import checks (fastapi, sqlalchemy, pandas)
  - Pytest tests with coverage
  - Docker image build test

frontend:
  - Setup Node.js 18
  - npm install --legacy-peer-deps ✅ Fixed v2.15.1
  - ESLint (if configured)
  - npm run build
  - Docker image build test

docker-compose:
  - Validate docker-compose.yml
```

#### 2. **Security Scan** (`.github/workflows/security.yml`)

**Frequency:** Weekly + on push

**Scans:**
- Trivy filesystem scan
- Trivy Docker images scan
- Python Safety check
- NPM audit

#### 3. **Release Workflow** (`.github/workflows/release.yml`)

**Trigger:** Tag push (`v*`)

**Actions:**
- Create source archive (tar.gz)
- Generate release notes from `RELEASE_NOTES_v*.md`
- Build and push Docker images to GHCR:
  - `ghcr.io/newwdead/crm/backend:version`
  - `ghcr.io/newwdead/crm/frontend:version`
  - `ghcr.io/newwdead/crm/backend:latest`
  - `ghcr.io/newwdead/crm/frontend:latest`

### Docker Configuration

**Main Services:**
- `docker-compose.yml` - Core services
- `docker-compose.prod.yml` - Production overrides
- `docker-compose.monitoring.yml` - Monitoring stack

**Networks:**
- `bizcard-network` - Internal communication

**Volumes:**
- `postgres_data` - Database persistence
- `redis_data` - Redis persistence
- `uploads` - User uploads
- `prometheus_data` - Metrics data
- `grafana_data` - Dashboard configs

---

## 💡 Рекомендации для разработки

### Общие принципы (из Cursor AI Rules)

#### Backend
✅ **DO:**
- Использовать async/await для DB операций
- Следовать паттерну: router → service → repository
- Использовать Depends() для DI
- Логировать важные операции
- Добавлять Prometheus метрики

❌ **DON'T:**
- Использовать raw SQL запросы
- Создавать новые большие файлы (>300 строк)
- Дублировать логику
- Редактировать конфигурации без явного запроса

#### Frontend
✅ **DO:**
- Использовать функциональные компоненты с хуками
- Tailwind CSS для стилей
- Axios для API
- React Router для навигации
- Избегать компонентов >300 строк

❌ **DON'T:**
- Создавать новые большие компоненты
- Использовать TypeScript (проект на JavaScript)
- Изменять структуру без необходимости

### Приоритетные задачи для улучшения

1. **Рефакторинг `main.py`** (HIGH)
   - Переместить оставшиеся endpoints в `api/`
   - Создать service layer для всех entities
   - Цель: < 500 строк в `main.py`

2. **Разбить большие React компоненты** (HIGH)
   - AdminPanel → подкомпоненты
   - ContactList → подкомпоненты
   - Улучшить переиспользуемость

3. **Централизовать Prometheus метрики** (MEDIUM)
   - Создать `core/metrics.py`
   - Переиспользовать метрики
   - Исправить дублирование

4. **Увеличить тестовое покрытие** (MEDIUM)
   - Unit тесты для services
   - Integration тесты для API
   - E2E тесты для критичных flow

5. **Добавить `package-lock.json`** (LOW)
   - Для reproducible builds
   - Улучшить CI stability

### Файлы, требующие внимания

| File | Size | Priority | Action |
|------|------|----------|--------|
| `backend/app/main.py` | 4072 lines | 🔴 HIGH | Refactor, split |
| `frontend/src/components/AdminPanel.js` | 1372 lines | 🔴 HIGH | Split into modules |
| `frontend/src/components/ContactList.js` | 1008 lines | 🔴 HIGH | Split into modules |
| `backend/app/api/contacts.py` | 419 lines | 🟡 MEDIUM | Review, optimize |
| `backend/app/tests/conftest.py` | 127 lines | ✅ OK | Recently fixed |

---

## 📝 Документация

### Доступная документация (52 файла)

**Guides:**
- `README.md` / `README.ru.md` - Main docs
- `ARCHITECTURE.md` - System architecture
- `AUTH_SETUP.md` - Authentication guide
- `TELEGRAM_SETUP.md` - Telegram integration
- `SSL_SETUP.md` - SSL configuration
- `PRODUCTION_DEPLOYMENT.md` - Deploy guide
- `MONITORING_SETUP.md` - Monitoring setup
- `SERVICE_LAYER_GUIDE.md` - Service layer patterns
- `TECHNICAL_DEBT.md` - Known issues

**Release Notes:**
- `RELEASE_NOTES_v*.md` - 15 release notes (v1.2 - v2.15.1)

**Recent Documents:**
- `CI_ERRORS_FIXED_SUMMARY.md` - v2.15.1 fixes
- `WORKFLOWS_PROBLEMS_AND_FIXES.md` - CI troubleshooting
- `GITHUB_ACTIONS_ANALYSIS.md` - CI analysis

---

## 🎯 Quick Start для новых разработчиков

### 1. Setup локального окружения

```bash
# Clone repository
git clone <repo-url>
cd fastapi-bizcard-crm-ready

# Start services
docker compose up -d --build

# Check status
docker compose ps
docker compose logs -f backend

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Grafana: http://localhost:3001
```

### 2. Изучить структуру

```bash
# Backend
ls backend/app/api/      # API routes
ls backend/app/models/   # Database models
ls backend/app/services/ # Business logic

# Frontend
ls frontend/src/components/  # React components
```

### 3. Запустить тесты

```bash
# Backend tests
docker compose exec backend pytest app/tests/ -v

# Frontend tests (if configured)
cd frontend && npm test
```

### 4. Сделать изменения

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes...

# Commit
git add .
git commit -m "feat: Add my feature"

# Push and create PR
git push origin feature/my-feature
```

---

## 📞 Контакты и поддержка

- **GitHub:** https://github.com/newwdead/CRM
- **Issues:** https://github.com/newwdead/CRM/issues
- **Actions:** https://github.com/newwdead/CRM/actions

---

## ✅ Checklist для следующей работы

- [ ] Изучить `backend/app/main.py` (4072 строки)
- [ ] Ознакомиться с `api/` routes structure
- [ ] Понять Service Layer pattern (`services/`)
- [ ] Изучить OCR систему (`ocr_providers.py`, `ocr_utils.py`)
- [ ] Проверить `TECHNICAL_DEBT.md` для понимания проблем
- [ ] Изучить большие React компоненты (AdminPanel, ContactList)
- [ ] Понять CI/CD workflows (`.github/workflows/`)
- [ ] Ознакомиться с monitoring stack (Prometheus, Grafana)

---

**Generated by:** Cursor AI Assistant  
**Date:** 21 октября 2025  
**Purpose:** Knowledge base for future development

**Status:** ✅ Ready for production development

