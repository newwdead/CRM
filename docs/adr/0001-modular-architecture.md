# ADR-0001: Modular Backend Architecture

**Status:** Accepted  
**Date:** 2025-10-21  
**Deciders:** Development Team  
**Technical Story:** Refactoring monolithic `main.py`

## Context

The backend `main.py` grew to 4000+ lines, containing:
- All API endpoints
- Business logic
- Database models
- Configuration
- Utility functions

This monolithic structure caused:
- Difficult maintenance and debugging
- Slow development velocity
- Hard to test individual components
- Code conflicts in team collaboration
- Unclear boundaries between components

## Decision

We will refactor the backend into a modular architecture:

```
backend/app/
├── api/           # API endpoints (by domain)
│   ├── auth.py
│   ├── contacts.py
│   ├── duplicates.py
│   └── admin.py
├── core/          # Core functionality
│   ├── config.py
│   ├── security.py
│   └── utils.py
├── models/        # Database models
│   ├── user.py
│   ├── contact.py
│   └── ...
├── schemas/       # Pydantic schemas
│   ├── user.py
│   ├── contact.py
│   └── ...
├── services/      # Business logic (future)
└── tests/         # Test suite
```

## Rationale

**Benefits:**
1. **Maintainability:** Smaller, focused modules
2. **Testability:** Easy to test individual components
3. **Scalability:** Clear structure for adding features
4. **Team Collaboration:** Fewer merge conflicts
5. **Code Quality:** Single Responsibility Principle

**Trade-offs:**
- Initial refactoring effort (~16 hours)
- Need to update imports throughout codebase
- Temporary increase in file count

## Consequences

### Positive
- Reduced `main.py` from 4000+ to ~500 lines
- Clear separation of concerns
- Easier onboarding for new developers
- Better IDE support and navigation
- Improved test coverage capability

### Negative
- More files to navigate
- Need to understand module structure
- Requires consistent patterns

### Neutral
- Migration period with mixed old/new code
- Documentation updates required

## Implementation

**Phase 1:** (Completed)
- ✅ Split models into 7 modules
- ✅ Split schemas into 6 modules
- ✅ Create api/ structure (3 modules)
- ✅ Create core/ utilities

**Phase 2:** (Planned)
- [ ] Extract remaining endpoints
- [ ] Create service layer
- [ ] Add comprehensive tests

## Alternatives Considered

### 1. Keep Monolithic Structure
**Rejected:** Unsustainable as project grows

### 2. Microservices
**Rejected:** Overkill for current scale, adds operational complexity

### 3. Modular Monolith
**Accepted:** Best balance of simplicity and maintainability

## References

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- Project: `/backend/app/api/`, `/backend/app/core/`

