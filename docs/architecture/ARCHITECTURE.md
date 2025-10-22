# System Architecture

**FastAPI Business Card CRM**  
**Version:** v2.12  
**Last Updated:** October 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Context](#system-context)
3. [Container Architecture](#container-architecture)
4. [Component Architecture](#component-architecture)
5. [Data Model](#data-model)
6. [API Design](#api-design)
7. [Security](#security)
8. [Performance & Scalability](#performance--scalability)
9. [Deployment](#deployment)
10. [Monitoring](#monitoring)

---

## Overview

### Purpose

FastAPI Business Card CRM is a web-based system for managing business card contacts with OCR processing, duplicate detection, and multi-channel integrations (Telegram, WhatsApp).

### Key Features

- 📇 **Contact Management:** CRUD operations with tags, groups
- 🔍 **OCR Processing:** Tesseract, Google Vision, PaddleOCR
- 🔗 **Duplicate Detection:** Fuzzy matching with configurable thresholds
- 💬 **Integrations:** Telegram Bot, WhatsApp webhooks
- 📊 **Monitoring:** Prometheus metrics, Grafana dashboards
- 🔐 **Authentication:** JWT-based auth with role-based access

---

## System Context

```
┌─────────────┐
│   Browser   │───────────────┐
└─────────────┘               │
                              │
┌─────────────┐               │
│   Mobile    │───────────────┤
└─────────────┘               │
                              │
┌─────────────┐               │
│  Telegram   │───────────┐   │
└─────────────┘           │   │
                          │   │
┌─────────────┐           │   ▼
│  WhatsApp   │───────────┤  ┌──────────────────────┐
└─────────────┘           │  │   FastAPI CRM        │
                          └─▶│   (Backend + UI)     │
┌─────────────┐              └──────────────────────┘
│   Admin     │───────────────────────▲
└─────────────┘                       │
                                      │
                              ┌───────┴────────┐
                              │                │
                         ┌────▼─────┐    ┌────▼─────┐
                         │PostgreSQL│    │  Redis   │
                         └──────────┘    └──────────┘
```

### External Dependencies

- **PostgreSQL:** Primary data store
- **Redis:** Celery broker, caching
- **Tesseract OCR:** Local OCR processing
- **Google Vision API:** Cloud OCR (optional)
- **PaddleOCR:** Advanced OCR (optional)
- **Telegram Bot API:** Bot integration
- **WhatsApp Business API:** Messaging integration

---

## Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Docker Compose                         │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Nginx     │  │   Frontend  │  │   Backend   │         │
│  │   (Proxy)   │  │   (React)   │  │  (FastAPI)  │         │
│  │   :80       │  │   :3000     │  │   :8000     │         │
│  └──────┬──────┘  └─────────────┘  └──────┬──────┘         │
│         │                                   │                 │
│         └───────────────┬───────────────────┘                │
│                         │                                     │
│         ┌───────────────▼───────────────┐                    │
│         │                               │                    │
│  ┌──────▼──────┐  ┌──────────────┐  ┌─▼─────────┐          │
│  │ PostgreSQL  │  │    Redis     │  │  Celery   │          │
│  │   :5432     │  │    :6379     │  │  Worker   │          │
│  └─────────────┘  └──────────────┘  └───────────┘          │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐                          │
│  │ Prometheus  │  │   Grafana    │                          │
│  │   :9090     │  │    :3001     │                          │
│  └─────────────┘  └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Services

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **nginx** | Nginx 1.24 | 80 | Reverse proxy, static files |
| **frontend** | React 18 | 3000 | User interface |
| **backend** | FastAPI + Python 3.10 | 8000 | API server |
| **db** | PostgreSQL 15 | 5432 | Primary database |
| **redis** | Redis 7 | 6379 | Cache, Celery broker |
| **celery** | Celery 5.3 | - | Background tasks |
| **prometheus** | Prometheus | 9090 | Metrics collection |
| **grafana** | Grafana | 3001 | Metrics visualization |

---

## Component Architecture

### Backend (FastAPI)

```
backend/app/
├── api/                    # REST API endpoints
│   ├── auth.py            # Authentication (JWT)
│   ├── contacts.py        # Contact CRUD
│   ├── duplicates.py      # Duplicate detection
│   └── __init__.py        # Router aggregation
│
├── core/                   # Core functionality
│   ├── config.py          # Configuration
│   ├── security.py        # Auth helpers
│   └── utils.py           # Audit log, settings
│
├── models/                 # SQLAlchemy models
│   ├── base.py            # Base & associations
│   ├── user.py            # User model
│   ├── contact.py         # Contact, Tag, Group
│   ├── duplicate.py       # DuplicateContact
│   ├── settings.py        # AppSetting, SystemSettings
│   ├── audit.py           # AuditLog
│   └── ocr.py             # OCRCorrection
│
├── schemas/                # Pydantic schemas
│   ├── user.py            # User DTOs
│   ├── contact.py         # Contact DTOs
│   ├── duplicate.py       # Duplicate DTOs
│   └── audit.py           # Audit DTOs
│
├── tests/                  # Test suite
│   ├── conftest.py        # Pytest fixtures
│   ├── test_duplicate_utils.py
│   ├── test_phone_utils.py
│   └── test_api_basic.py
│
├── main.py                 # FastAPI app initialization
├── database.py             # Database connection
├── duplicate_utils.py      # Duplicate detection logic
├── phone_utils.py          # Phone formatting
├── ocr_providers.py        # OCR provider management
├── telegram_polling.py     # Telegram bot
└── tasks.py                # Celery tasks
```

### Frontend (React)

```
frontend/src/
├── components/
│   ├── AdminPanel.js       # Admin dashboard
│   ├── ContactList.js      # Contact table
│   ├── ContactForm.js      # Create/edit contact
│   ├── DuplicateMergeModal.js
│   ├── DuplicatesPanel.js
│   ├── OCREditorWithBlocks.js
│   ├── TableSettings.js
│   └── SearchOverlay.js
│
├── translations/
│   └── translations.js     # i18n
│
├── App.js                  # Main component
└── index.js                # Entry point
```

---

## Data Model

### Entity-Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │   Contact   │       │     Tag     │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │       │ id          │       │ id          │
│ username    │       │ full_name   │       │ name        │
│ email       │       │ email       │       │ color       │
│ password    │       │ phone       │       └──────┬──────┘
│ is_admin    │       │ company     │              │
│ is_active   │       │ position    │              │
└──────┬──────┘       │ created_at  │              │
       │              │ uid         │              │
       │              │ sequence_number│           │
       │              └──────┬──────┘              │
       │                     │                     │
       │                     │◄────────────────────┘
       │                     │    contact_tags
       │                     │
       │              ┌──────▼──────┐
       │              │  AuditLog   │
       │              ├─────────────┤
       │              │ id          │
       │◄─────────────┤ user_id     │
       │              │ contact_id  │
       │              │ action      │
       │              │ changes     │
       │              │ timestamp   │
       │              └─────────────┘
       │
       │              ┌─────────────────┐
       │              │ DuplicateContact│
       │              ├─────────────────┤
       │              │ id              │
       │◄─────────────┤ reviewed_by     │
                      │ contact_id_1    │
                      │ contact_id_2    │
                      │ similarity_score│
                      │ status          │
                      │ match_fields    │
                      └─────────────────┘
```

### Key Tables

**users**
- Authentication and authorization
- Admin vs regular user roles

**contacts**
- Core business card data
- Sequential numbering
- UID for external references

**contact_tags** (many-to-many)
- Flexible categorization

**contact_groups** (many-to-many)
- Organization by groups

**duplicate_contacts**
- Detected duplicate pairs
- Similarity scores and matched fields
- Review workflow (pending/reviewed/merged/ignored)

**audit_log**
- Complete audit trail
- User actions tracking

---

## API Design

### REST Endpoints

**Authentication:**
```
POST   /auth/register          # User registration
POST   /auth/login             # Login (JWT)
GET    /auth/me                # Current user
PUT    /auth/me                # Update profile
GET    /auth/users             # List users (admin)
```

**Contacts:**
```
GET    /contacts/              # List (paginated, filtered)
POST   /contacts/              # Create
GET    /contacts/{id}          # Get by ID
PUT    /contacts/{id}          # Update
DELETE /contacts/{id}          # Delete
GET    /contacts/search/       # Fast search
GET    /contacts/{id}/history  # Audit log
```

**Duplicates:**
```
GET    /api/duplicates                    # List detected
POST   /api/duplicates/find              # Manual scan
PUT    /api/duplicates/{id}/status       # Update status
POST   /api/duplicates/merge/{id1}/{id2} # Merge contacts
```

### Response Format

**Success:**
```json
{
  "id": 123,
  "full_name": "John Doe",
  "email": "john@example.com",
  "created_at": "2025-10-21T10:00:00Z"
}
```

**Error:**
```json
{
  "detail": "Contact not found"
}
```

**Paginated:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

---

## Security

### Authentication Flow

```
┌────────┐                  ┌────────┐                  ┌────────┐
│ Client │                  │Backend │                  │Database│
└───┬────┘                  └───┬────┘                  └───┬────┘
    │                           │                           │
    │ POST /auth/login          │                           │
    ├──────────────────────────►│                           │
    │ {username, password}      │                           │
    │                           │ Verify credentials        │
    │                           ├──────────────────────────►│
    │                           │                           │
    │                           │◄──────────────────────────┤
    │◄──────────────────────────┤ User data                 │
    │ {access_token, ...}       │                           │
    │                           │                           │
    │ GET /contacts/            │                           │
    ├──────────────────────────►│                           │
    │ Authorization: Bearer ... │                           │
    │                           │ Verify JWT                │
    │                           │                           │
    │◄──────────────────────────┤                           │
    │ [contacts...]             │                           │
```

### Security Measures

**1. Authentication:**
- JWT tokens (30-minute expiry)
- Password hashing (bcrypt)
- OAuth2 password flow

**2. Authorization:**
- Role-based access control (admin/user)
- Endpoint-level permissions
- User activation workflow

**3. Rate Limiting:**
- IP-based limits
- Per-endpoint throttling
- Configurable thresholds

**4. Input Validation:**
- Pydantic schema validation
- SQL injection prevention (ORM)
- XSS protection

**5. CORS:**
- Whitelisted origins
- Credential support
- Method restrictions

---

## Performance & Scalability

### Current Performance

**Response Times:**
- Health check: <10ms
- Contact list: 50-200ms
- OCR processing: 1-5s
- Duplicate detection: 100-500ms

**Throughput:**
- 100+ req/sec (gunicorn workers)
- 1000s of contacts in database
- Real-time duplicate detection

### Optimization Strategies

**1. Database:**
- Indexes on frequently queried fields
- Connection pooling
- Query optimization (N+1 prevention)

**2. Caching:**
- Redis for session data
- OCR results caching
- Static file caching (nginx)

**3. Background Processing:**
- Celery for OCR tasks
- Async duplicate detection
- Scheduled maintenance tasks

**4. Frontend:**
- Code splitting
- Lazy loading
- Image optimization

### Scalability Path

**Current (v2.12):**
- Single server
- Docker Compose
- ~1000 contacts, <20 users

**Next Steps:**
- **Horizontal Scaling:** Multiple backend instances
- **Database Replication:** Read replicas
- **CDN:** Static file distribution
- **Load Balancer:** Nginx/HAProxy

**Future (v3.0+):**
- Kubernetes orchestration
- Multi-region deployment
- Elasticsearch for search
- Microservices architecture

---

## Deployment

### Docker Compose (Current)

**Production Stack:**
```yaml
services:
  nginx:      # Reverse proxy
  frontend:   # React app
  backend:    # FastAPI
  db:         # PostgreSQL
  redis:      # Cache/broker
  celery:     # Background worker
  prometheus: # Metrics
  grafana:    # Dashboards
```

**Deployment Steps:**
```bash
# 1. Clone repository
git clone ...
cd fastapi-bizcard-crm

# 2. Configure environment
cp .env.example .env
# Edit .env

# 3. Start services
docker compose up -d

# 4. Run migrations
docker compose exec backend python -c "from app.database import init_db; init_db()"

# 5. Verify
curl http://localhost/health
```

### CI/CD Pipeline

**GitHub Actions Workflows:**

1. **CI** (`.github/workflows/ci.yml`):
   - Lint code
   - Run tests
   - Build Docker images

2. **Release** (`.github/workflows/release.yml`):
   - Create GitHub release
   - Build & push Docker images
   - Generate changelog

3. **Security** (`.github/workflows/security.yml`):
   - Trivy vulnerability scan
   - Dependency audit

---

## Monitoring

### Metrics (Prometheus)

**Application Metrics:**
- `http_requests_total` - Request count
- `http_request_duration_seconds` - Response time
- `ocr_processing_total` - OCR operations
- `contacts_total` - Contact count
- `auth_attempts_total` - Login attempts

**System Metrics:**
- CPU usage
- Memory usage
- Disk I/O
- Network traffic

### Dashboards (Grafana)

**Main Dashboard:**
- Request rate & latency
- Error rates
- Active users
- Database connections

**Business Metrics:**
- Contacts created/day
- OCR success rate
- Duplicate detection stats

### Alerts

**Critical:**
- Service down
- Database unreachable
- High error rate (>5%)

**Warning:**
- High response time (>1s)
- Disk space <20%
- Memory usage >80%

### Logging

**Structured Logging:**
```python
logger.info("Contact created", extra={
    "user_id": user.id,
    "contact_id": contact.id,
    "action": "create"
})
```

**Log Aggregation:**
- Docker logs
- Centralized logging (future: ELK stack)

---

## Architecture Decisions

See [docs/adr/](docs/adr/) for detailed Architecture Decision Records:

- [ADR-0001: Modular Backend Architecture](docs/adr/0001-modular-architecture.md)
- [ADR-0002: Duplicate Detection Strategy](docs/adr/0002-duplicate-detection-strategy.md)

---

## Future Roadmap

### v2.14
- Complete service layer refactoring
- Improve test coverage (40%+)
- Performance optimization

### v2.15
- Frontend component refactoring
- Alembic database migrations
- Advanced duplicate detection

### v3.0
- Microservices architecture
- Multi-tenancy support
- Advanced analytics
- Mobile app (React Native)

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)

---

**Last Updated:** 2025-10-21  
**Maintainers:** Development Team  
**Questions?** See [CONTRIBUTING.md](CONTRIBUTING.md)

