# 📚 Documentation Index - FastAPI Business Card CRM

## 📖 Quick Navigation

### 🚀 Getting Started
- [README](../README.md) - Main project documentation
- [README.ru](../README.ru.md) - Документация на русском
- [Quick Start Guide](guides/QUICK_START_MODULES.md) - Модульная структура проекта
- [System Check](guides/SYSTEM_CHECK.md) - Проверка системы

### 🔒 Security
- [SECURITY.md](../SECURITY.md) - Security policy and vulnerability reporting
- [Phase 1 Security Complete](technical/PHASE1_COMPLETE_v3.5.1.md) - v3.5.1 Security hardening

### 🏗️ Technical Documentation
- [Monitoring Setup](technical/MONITORING_SETUP_v3.7.0.md) - v3.7.0 Structured logging
- [Performance Improvements](technical/PERFORMANCE_IMPROVEMENTS.md) - Optimization guide
- [Repository Migration Plan](technical/REPOSITORY_MIGRATION_PLAN.md) - 3-layer architecture

### 📦 Archived Documentation
All historical documentation (v2.x - v3.6.x) is archived in [`archive/`](archive/) directory.

---

## 📂 Directory Structure

```
docs/
├── INDEX.md (this file)
├── guides/           # User guides and quick starts
├── technical/        # Technical documentation and architecture
└── archive/          # Historical releases and old docs (48 files)
```

---

## 🎯 Current Version: v3.7.0

**Latest Features:**
- ✅ Structured JSON logging
- ✅ Request tracking with unique IDs
- ✅ Performance monitoring
- ✅ Error tracking with stack traces

**Documentation:**
- [Monitoring Setup v3.7.0](technical/MONITORING_SETUP_v3.7.0.md)

---

## 📊 Project Phases

### Phase 1: Security Hardening (v3.5.x) ✅
- 2FA implementation
- JWT refresh tokens
- File upload security
- Security testing

**Documentation:** [PHASE1_COMPLETE_v3.5.1.md](technical/PHASE1_COMPLETE_v3.5.1.md)

### Phase 2: Architecture Optimization (v3.6.x - v3.7.0) ✅
- Backend refactoring (core/ + integrations/)
- Database optimization (25+ indexes)
- Frontend performance (React.memo)
- Docker optimization (-7% size)
- Monitoring setup (JSON logs)

**Documentation:** 
- [Monitoring Setup v3.7.0](technical/MONITORING_SETUP_v3.7.0.md)
- See [archive/](archive/) for individual releases

### Phase 3: Cleanup & Documentation (v3.7.x) 🚧
- Documentation organization
- Dead code removal
- Asset optimization
- Test reorganization

### Phase 4: Dependency Updates (v4.0.0) 📋
- Python dependencies (FastAPI, SQLAlchemy)
- Node.js dependencies (React ecosystem)
- Docker images (Python 3.11, Node 20)
- Full testing & validation

---

## 🔍 Finding Documentation

**By Topic:**
- **Setup & Installation:** [README.md](../README.md)
- **Security:** [SECURITY.md](../SECURITY.md) + [technical/](technical/)
- **Architecture:** [technical/](technical/)
- **Monitoring:** [technical/MONITORING_SETUP_v3.7.0.md](technical/MONITORING_SETUP_v3.7.0.md)

**By Version:**
- **Current (v3.7.0):** [technical/](technical/)
- **Previous (v2.x - v3.6.x):** [archive/](archive/)

**By Date:**
All archived docs are sorted chronologically by version number.

---

## 📝 Contributing

When adding new documentation:
1. Place in appropriate directory (guides/, technical/, or archive/)
2. Update this INDEX.md
3. Follow naming convention: `TITLE_vX.Y.Z.md` for versioned docs
4. Use clear, descriptive titles

---

## 🏆 Milestones

| Version | Date | Milestone |
|---------|------|-----------|
| v3.7.0 | 2025-10-24 | Phase 2 Complete: Monitoring & Logging |
| v3.6.3 | 2025-10-24 | Docker Optimization |
| v3.6.2 | 2025-10-24 | Frontend Performance |
| v3.6.1 | 2025-10-24 | Database Optimization |
| v3.6.0 | 2025-10-24 | Backend Refactoring |
| v3.5.1 | 2025-10 | Phase 1 Complete: Security Hardening |
| v3.0.0 | 2025-10 | Repository Layer Migration |

---

## 📧 Support

- **Issues:** GitHub Issues
- **Security:** See [SECURITY.md](../SECURITY.md)
- **General:** Project README

---

*Last Updated: 2025-10-24 (v3.7.0)*

