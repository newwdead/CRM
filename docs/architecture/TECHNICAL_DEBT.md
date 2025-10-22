# Technical Debt Register

This document tracks known technical debt, performance issues, and areas for improvement.

**Last Updated:** October 2025  
**Version:** v2.12

---

## 🚨 High Priority

### 1. Monolithic `main.py` (Partially Addressed)

**Status:** 🟡 In Progress  
**Impact:** High  
**Effort:** Medium

**Issue:**
- `main.py` still contains 4000+ lines of code
- Mixing of business logic, routing, and configuration
- Difficult to maintain and test

**Progress:**
- ✅ Split models into 7 modules (`models/`)
- ✅ Split schemas into 6 modules (`schemas/`)
- ✅ Created modular API structure (`api/`)
- ✅ Created core utilities (`core/`)
- ⏳ Still need to extract remaining endpoints

**Next Steps:**
- [ ] Move admin endpoints to `api/admin.py`
- [ ] Move OCR endpoints to `api/ocr.py`
- [ ] Move settings endpoints to `api/settings.py`
- [ ] Create service layer for business logic
- [ ] Reduce `main.py` to < 500 lines

### 2. Large Frontend Components

**Status:** 🔴 Not Started  
**Impact:** High  
**Effort:** Medium

**Issue:**
- `AdminPanel.js` - 1372 lines
- `ContactList.js` - 1008 lines
- Single-responsibility principle violated
- Hard to test and maintain

**Solution:**
```
frontend/src/components/
├── AdminPanel/
│   ├── index.js
│   ├── UsersTab.js
│   ├── SettingsTab.js
│   ├── DocumentationTab.js
│   └── DuplicatesTab.js
└── ContactList/
    ├── index.js
    ├── ContactTable.js
    ├── ContactFilters.js
    └── ContactActions.js
```

**Effort Estimate:** 8-12 hours

### 3. Prometheus Metrics Duplication

**Status:** 🟡 Partially Fixed  
**Impact:** Medium  
**Effort:** Low

**Issue:**
- Metrics defined in multiple places
- Causes `ValueError: Duplicated timeseries` errors
- Currently commented out in refactored modules

**Solution:**
- Create centralized `metrics.py` module
- Import metrics from single source
- Re-enable metrics in API modules

**Next Steps:**
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Gauge

# Define all metrics once
auth_attempts_counter = Counter(...)
contacts_total = Gauge(...)

# Import in API modules
from ..core.metrics import auth_attempts_counter
```

---

## 🟡 Medium Priority

### 4. Missing Service Layer

**Status:** 🔴 Not Started  
**Impact:** Medium  
**Effort:** High

**Issue:**
- Business logic mixed with API endpoints
- Difficult to reuse logic
- Hard to test in isolation

**Proposed Structure:**
```
backend/app/services/
├── __init__.py
├── contact_service.py
├── duplicate_service.py
├── ocr_service.py
└── auth_service.py
```

**Benefits:**
- Cleaner separation of concerns
- Easier testing
- Better code reuse
- Facilitates future features (CLI, scheduled tasks)

**Effort Estimate:** 16-24 hours

### 5. Database Migration Strategy

**Status:** 🟡 Hybrid Approach  
**Impact:** Medium  
**Effort:** Medium

**Issue:**
- Mix of SQL scripts and in-app migrations
- No Alembic integration
- Manual migration tracking

**Current Approach:**
```
backend/migrations/
├── add_sequence_number.sql
├── create_duplicates_table.sql
└── ...
```

**Proposed Solution:**
- Implement Alembic for migrations
- Convert existing SQL to Alembic versions
- Auto-generate migrations from model changes

**Effort Estimate:** 12-16 hours

### 6. Test Coverage

**Status:** 🟢 Started (v2.13)  
**Impact:** Medium  
**Effort:** Medium

**Current Coverage:** ~15%  
**Target Coverage:** 70%+

**Progress:**
- ✅ Pytest infrastructure setup
- ✅ Unit tests for `duplicate_utils`
- ✅ Unit tests for `phone_utils`
- ✅ Basic integration tests
- ⏳ Missing coverage for major features

**Gaps:**
- OCR processing (0% coverage)
- Telegram integration (0% coverage)
- WhatsApp integration (0% coverage)
- Admin endpoints (0% coverage)
- Frontend (0% coverage)

---

## 🟢 Low Priority

### 7. Frontend State Management

**Status:** 🔴 Not Started  
**Impact:** Low  
**Effort:** High

**Issue:**
- No centralized state management
- Props drilling in component tree
- Duplicate API calls

**Consideration:**
- Evaluate if complexity warrants Redux/Zustand
- Current approach may be sufficient for app size

### 8. API Versioning

**Status:** 🔴 Not Implemented  
**Impact:** Low  
**Effort:** Low

**Issue:**
- No API versioning strategy
- Breaking changes affect all clients

**Proposed:**
```
/api/v1/contacts/
/api/v2/contacts/
```

**Benefits:**
- Smoother API evolution
- Backward compatibility
- Gradual deprecation

### 9. Error Handling Standardization

**Status:** 🟡 Inconsistent  
**Impact:** Low  
**Effort:** Low

**Issue:**
- Mix of HTTP exceptions, custom exceptions, and error returns
- No standardized error response format

**Proposed:**
```json
{
  "error": {
    "code": "CONTACT_NOT_FOUND",
    "message": "Contact with ID 123 not found",
    "details": {...}
  }
}
```

---

## 📊 Performance Issues

### 10. N+1 Query Problems

**Status:** 🔴 Known Issue  
**Impact:** Medium  
**Effort:** Medium

**Location:**
- Contact list with tags/groups
- Duplicate detection queries

**Solution:**
- Use SQLAlchemy `joinedload` / `selectinload`
- Add query logging to identify bottlenecks

**Example:**
```python
# Before (N+1)
contacts = db.query(Contact).all()
for c in contacts:
    tags = c.tags  # Separate query for each contact

# After (1 query)
contacts = db.query(Contact).options(
    joinedload(Contact.tags)
).all()
```

### 11. Large File Upload Performance

**Status:** 🔴 Known Issue  
**Impact:** Low  
**Effort:** Medium

**Issue:**
- Synchronous upload handling
- No streaming for large files
- Memory spikes on multiple uploads

**Solution:**
- Implement streaming uploads
- Add background processing for large batches
- Use Celery for OCR processing

---

## 🔐 Security Concerns

### 12. Rate Limiting Granularity

**Status:** 🟢 Basic Implementation  
**Impact:** Medium  
**Effort:** Low

**Current:**
- IP-based rate limiting
- Global limits per endpoint

**Improvement:**
- Per-user rate limiting
- Configurable limits per role
- Burst allowances

### 13. Input Validation

**Status:** 🟡 Partial  
**Impact:** Medium  
**Effort:** Low

**Issue:**
- Reliance on Pydantic for validation
- Some endpoints lack thorough validation
- File upload validation needs improvement

**Next Steps:**
- Add file type/size validation
- Sanitize all user inputs
- Add schema validation for JSON fields

---

## 📝 Documentation Gaps

### 14. API Documentation

**Status:** 🟡 Auto-generated Only  
**Impact:** Low  
**Effort:** Medium

**Current:**
- Swagger/OpenAPI auto-docs only
- No usage examples
- No authentication guide

**Needs:**
- Getting Started guide
- Authentication flow documentation
- Common use cases with examples
- Error handling guide

### 15. Architecture Documentation

**Status:** 🟢 In Progress (v2.13)  
**Impact:** Low  
**Effort:** Low

**Progress:**
- ⏳ ARCHITECTURE.md being created
- ⏳ ADR documents being created
- ✅ CONTRIBUTING.md created
- ✅ TECHNICAL_DEBT.md created

---

## 📅 Debt Reduction Roadmap

### v2.13 (Current)
- ✅ Refactor models and schemas
- ✅ Create modular API structure
- ✅ Add pytest infrastructure
- ⏳ Complete documentation

### v2.14 (Next)
- [ ] Complete main.py refactoring
- [ ] Fix Prometheus metrics
- [ ] Improve test coverage to 40%
- [ ] Implement service layer

### v2.15
- [ ] Frontend component refactoring
- [ ] Implement Alembic migrations
- [ ] Test coverage to 70%
- [ ] Performance optimization

### v3.0 (Future)
- [ ] API versioning
- [ ] Comprehensive monitoring
- [ ] Advanced caching
- [ ] Multi-tenancy support

---

## 🎯 Effort vs Impact Matrix

```
High Impact, Low Effort:
- Fix Prometheus metrics
- Standardize error handling
- Add input validation

High Impact, High Effort:
- Complete main.py refactoring
- Implement service layer
- Frontend component split

Low Impact, Low Effort:
- API versioning
- Documentation improvements

Low Impact, High Effort:
- Frontend state management
- Comprehensive test coverage
```

---

## 📞 Contributing to Debt Reduction

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on tackling technical debt items.

**Priority Order:**
1. High Impact, Low Effort
2. High Impact, High Effort  
3. Low Impact, Low Effort
4. Low Impact, High Effort

---

**Note:** This is a living document. Update it as debt is addressed or new issues are discovered.

