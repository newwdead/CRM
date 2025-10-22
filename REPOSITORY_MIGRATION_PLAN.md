# 📋 Repository Layer Migration Plan

**Version:** 2.32.0  
**Date:** 2025-10-22  
**Status:** In Progress

---

## 🎯 Goal

Migrate all API endpoints to use Repository Layer instead of direct database access, following the 3-layer architecture pattern.

---

## 📊 Current State

### Completed ✅
- `ContactRepository` - ✅ Partially migrated
  - `/api/contacts` - Using ContactService & ContactRepository
  
### To Migrate ⏳

**OCR Endpoints** (`api/ocr.py`):
- [ ] Create OCR training data entries
- [ ] Use ContactRepository for contact creation
- [ ] Use OCRRepository for training data

**Duplicate Endpoints** (`api/duplicates.py`):
- [ ] `GET /duplicates` - List duplicates
- [ ] `POST /duplicates/find` - Find duplicates
- [ ] `PUT /duplicates/{id}/status` - Update status
- [ ] `POST /duplicates/{id}/ignore` - Ignore duplicate
- [ ] `POST /duplicates/merge` - Merge contacts

**User Endpoints** (`api/users.py`, `api/admin.py`):
- [ ] User CRUD operations
- [ ] User authentication
- [ ] User management

**Settings Endpoints** (`api/settings.py`, `api/admin.py`):
- [ ] Settings CRUD
- [ ] System configuration
- [ ] Integration settings

---

## 🏗️ Architecture Pattern

### Current (Direct DB Access):
```python
@router.get('/contacts')
def get_contacts(db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()  # ❌ Direct DB access
    return contacts
```

### Target (Repository Pattern):
```python
@router.get('/contacts')
def get_contacts(db: Session = Depends(get_db)):
    repo = ContactRepository(db)
    contacts = repo.get_all()  # ✅ Through repository
    return contacts
```

### Best (Service Layer):
```python
@router.get('/contacts')
def get_contacts(db: Session = Depends(get_db)):
    service = ContactService(db)
    contacts = service.get_contacts_list()  # ✅✅ Through service
    return contacts
```

---

## 📝 Migration Checklist

### Phase 1: Preparation ✅
- [x] Create all repositories
- [x] Add type hints & docstrings
- [x] Write repository tests
- [x] Create ContactService

### Phase 2: API Migration (In Progress)
- [x] Migrate `/api/contacts` endpoints
- [ ] Migrate `/api/ocr` endpoints
- [ ] Migrate `/api/duplicates` endpoints
- [ ] Migrate `/api/users` endpoints
- [ ] Migrate `/api/settings` endpoints

### Phase 3: Testing
- [ ] Update existing tests
- [ ] Add new integration tests
- [ ] Verify no direct DB access remains

### Phase 4: Documentation
- [ ] Update API documentation
- [ ] Update architecture diagrams
- [ ] Create migration guide

---

## 🔄 Migration Process

### Step 1: Identify Direct DB Access

Search patterns:
```python
db.query(Model)
db.add(model)
db.commit()
db.delete(model)
```

### Step 2: Create Service Method (if needed)

```python
class MyService:
    def __init__(self, db: Session):
        self.repo = MyRepository(db)
    
    def get_items(self, filters):
        return self.repo.find_all(filters)
```

### Step 3: Update Endpoint

```python
@router.get('/items')
def get_items(db: Session = Depends(get_db)):
    service = MyService(db)
    return service.get_items({})
```

### Step 4: Test

```python
def test_get_items(client, auth_token):
    response = client.get(
        "/api/items",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
```

---

## 📊 Progress Tracking

| Module | Endpoints | Migrated | Progress |
|--------|-----------|----------|----------|
| Contacts | 15 | 15 | 100% ✅ |
| OCR | 5 | 0 | 0% ⏳ |
| Duplicates | 6 | 0 | 0% ⏳ |
| Users | 8 | 0 | 0% ⏳ |
| Settings | 10 | 0 | 0% ⏳ |
| **Total** | **44** | **15** | **34%** |

---

## 🚀 Quick Reference

### Import Repositories

```python
from ..repositories import (
    ContactRepository,
    DuplicateRepository,
    UserRepository,
    OCRRepository,
    SettingsRepository,
    AuditRepository
)
```

### Create Service

```python
from ..services import ContactService

service = ContactService(db)
```

### Common Patterns

**Get by ID:**
```python
# Before
contact = db.query(Contact).filter(Contact.id == id).first()

# After
repo = ContactRepository(db)
contact = repo.get_by_id(id)
```

**Create:**
```python
# Before
contact = Contact(**data)
db.add(contact)
db.commit()

# After
repo = ContactRepository(db)
contact = repo.create(data)
repo.commit()
```

**Update:**
```python
# Before
contact.name = new_name
db.commit()

# After
repo = ContactRepository(db)
contact = repo.update(id, {"name": new_name})
repo.commit()
```

**Delete:**
```python
# Before
db.delete(contact)
db.commit()

# After
repo = ContactRepository(db)
repo.delete(contact)
repo.commit()
```

---

## ✅ Benefits

1. **Separation of Concerns**
   - API layer handles HTTP
   - Service layer handles business logic
   - Repository handles data access

2. **Testability**
   - Easy to mock repositories
   - Test business logic independently
   - Test data access separately

3. **Maintainability**
   - Changes in one layer don't affect others
   - Easy to find and fix bugs
   - Clear code organization

4. **Reusability**
   - Repositories reused across endpoints
   - Services reused in different contexts
   - Consistent data access patterns

---

**Status:** In Progress  
**Target:** v2.32.0  
**ETA:** Phase 2 completion

