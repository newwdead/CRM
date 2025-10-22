# 🏗️ Backend 3-Layer Pattern

**Version:** 2.22.0  
**Status:** ✅ Services Created, 🔄 Integration In Progress

---

## 📐 Архитектура

```
API Layer (Routers)           ← User requests, validation
    ↓
Service Layer (Business Logic) ← Core logic, orchestration
    ↓
Repository Layer (Data Access) ← Database operations
    ↓
Database (PostgreSQL)          ← Data storage
```

---

## 📊 Текущий статус

### ✅ Созданные сервисы:

| Service | Строк | Статус | Использование |
|---------|-------|--------|---------------|
| `contact_service.py` | 437 | ✅ Готов | ⚠️ Не интегрирован |
| `ocr_service.py` | 302 | ✅ Готов | ⚠️ Не интегрирован |
| `duplicate_service.py` | 349 | ✅ Готов | ⚠️ Не интегрирован |
| `settings_service.py` | 208 | ✅ Готов | ⚠️ Не интегрирован |

### ❌ Repository слой: НЕ создан

---

## 🎯 Преимущества 3-layer pattern

### 1. Изоляция логики ✅
```python
# ❌ БЕЗ services (всё в роутере):
@router.get('/contacts/')
def list_contacts(q: str, db: Session):
    # 100 строк бизнес-логики
    query = db.query(Contact)
    if q:
        query = query.filter(...)
    # ... еще 80 строк ...
    return contacts

# ✅ С services (роутер = 5 строк):
@router.get('/contacts/')
def list_contacts(q: str, db: Session):
    service = ContactService(db)
    return service.list_contacts(q=q)
```

### 2. Переиспользование 🔄
```python
# Сервис можно вызвать откуда угодно:
from ..services.contact_service import ContactService

# Из API
service = ContactService(db)
contacts = service.list_contacts(q="John")

# Из Celery задачи
@celery_app.task
def export_contacts():
    service = ContactService(db)
    contacts = service.list_contacts()

# Из админки
def admin_view(db):
    service = ContactService(db)
    return service.list_contacts(limit=1000)
```

### 3. Тестируемость 🧪
```python
# Легко тестировать без FastAPI/HTTP
def test_list_contacts():
    service = ContactService(mock_db)
    result = service.list_contacts(q="test")
    assert len(result['contacts']) == 3
```

---

## 📝 Структура файлов

```
backend/app/
├── api/                  # API Layer (Routers)
│   ├── contacts.py       # 593 строки → нужно рефакторить
│   ├── ocr.py            # 410 строк → нужно рефакторить
│   └── duplicates.py     # 460 строк → нужно рефакторить
│
├── services/             # Service Layer ✅ ГОТОВО
│   ├── __init__.py
│   ├── base.py           # Базовый класс
│   ├── contact_service.py   # 437 строк
│   ├── ocr_service.py        # 302 строки
│   ├── duplicate_service.py  # 349 строк
│   └── settings_service.py   # 208 строк
│
├── repositories/         # Repository Layer ❌ НЕТ
│   └── (нужно создать)
│
└── models/               # Database Models ✅ ГОТОВО
    └── ...
```

---

## 🔧 Как мигрировать endpoint

### Пример: GET /contacts/ (List Contacts)

#### 📌 ШАГ 1: Текущая реализация (API = 100 строк)

```python
# backend/app/api/contacts.py
@router.get('/', response_model=schemas.PaginatedContactsResponse)
def list_contacts(
    q: str = Query(None),
    company: str = Query(None),
    sort_by: str = Query('id'),
    page: int = Query(1),
    limit: int = Query(20),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    # Вся логика здесь (100 строк)
    query = db.query(Contact).options(
        joinedload(Contact.tags),
        joinedload(Contact.groups)
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (Contact.full_name.ilike(search_term)) |
            (Contact.company.ilike(search_term)) |
            # ... еще 20 строк фильтров
        )
    
    if company:
        query = query.filter(Contact.company.ilike(f"%{company}%"))
    
    # Сортировка (20 строк)
    if sort_by == 'full_name':
        query = query.order_by(...)
    elif sort_by == 'company':
        query = query.order_by(...)
    # ... еще 10 вариантов
    
    # Пагинация (10 строк)
    skip = (page - 1) * limit
    total = query.count()
    contacts = query.offset(skip).limit(limit).all()
    
    return {
        'total': total,
        'page': page,
        'limit': limit,
        'contacts': contacts
    }
```

#### 📌 ШАГ 2: Новая реализация (API = 10 строк, Service = 90 строк)

**API Router** (роутер только валидация + вызов сервиса):
```python
# backend/app/api/contacts.py
from ..services.contact_service import ContactService

@router.get('/', response_model=schemas.PaginatedContactsResponse)
def list_contacts(
    q: str = Query(None),
    company: str = Query(None),
    sort_by: str = Query('id'),
    page: int = Query(1),
    limit: int = Query(20),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """Get paginated list of contacts with search and filtering."""
    service = ContactService(db)
    return service.list_contacts(
        q=q, company=company, sort_by=sort_by, 
        page=page, limit=limit
    )
```

**Service** (вся логика):
```python
# backend/app/services/contact_service.py
class ContactService(BaseService):
    def list_contacts(
        self,
        q: Optional[str] = None,
        company: Optional[str] = None,
        sort_by: str = 'id',
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated list of contacts.
        All business logic is here.
        """
        # Query building
        query = self.db.query(Contact).options(
            joinedload(Contact.tags),
            joinedload(Contact.groups)
        )
        
        # Filters
        if q:
            query = self._apply_search_filter(query, q)
        
        if company:
            query = query.filter(Contact.company.ilike(f"%{company}%"))
        
        # Sorting
        query = self._apply_sorting(query, sort_by)
        
        # Pagination
        return self._paginate(query, page, limit)
```

### ✅ Результат:
- **Роутер:** 593 строки → **10 строк** (-98%)
- **Сервис:** уже есть
- **Переиспользование:** можно вызвать из любого места
- **Тестирование:** легко

---

## 📋 Миграционный чеклист

### Для contacts.py:

- [ ] ✅ ContactService уже существует (437 строк)
- [x] Импортировать ContactService в contacts.py
- [ ] Переписать 11 endpoint'ов:
  - [ ] `GET /` - list_contacts
  - [ ] `GET /search/` - search_contacts
  - [ ] `GET /{id}` - get_contact
  - [ ] `GET /uid/{uid}` - get_contact_by_uid
  - [ ] `POST /` - create_contact
  - [ ] `PUT /{id}` - update_contact
  - [ ] `DELETE /{id}` - delete_contact
  - [ ] `GET /{id}/history` - get_contact_history
  - [ ] `GET /{id}/ocr-blocks` - get_ocr_blocks
  - [ ] `POST /{id}/ocr-corrections` - save_ocr_corrections
  - [ ] `POST /{id}/reprocess-ocr` - reprocess_ocr

### Для ocr.py:

- [ ] ✅ OCRService уже существует (302 строки)
- [ ] Импортировать OCRService
- [ ] Переписать 10 endpoint'ов

### Для duplicates.py:

- [ ] ✅ DuplicateService уже существует (349 строк)
- [ ] Импортировать DuplicateService
- [ ] Переписать 12 endpoint'ов

---

## 🚀 Template для миграции endpoint'а

```python
# ДО (в роутере):
@router.get('/resource/')
def get_resource(
    param: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    # 50 строк логики
    query = db.query(Model)
    query = query.filter(...)
    # ... много кода ...
    return result

# ПОСЛЕ (в роутере):
from ..services.resource_service import ResourceService

@router.get('/resource/')
def get_resource(
    param: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """Get resource with param."""
    service = ResourceService(db)
    return service.get_resource(param=param)

# В сервисе (services/resource_service.py):
class ResourceService(BaseService):
    def get_resource(self, param: Optional[str] = None) -> Dict[str, Any]:
        """Business logic here."""
        query = self.db.query(Model)
        if param:
            query = query.filter(Model.field == param)
        return query.all()
```

---

## 💡 Следующие шаги

### Фаза 1: Интеграция Services (1-2 дня)
1. Переписать все endpoint'ы в `contacts.py` (11 шт.)
2. Переписать все endpoint'ы в `ocr.py` (10 шт.)
3. Переписать все endpoint'ы в `duplicates.py` (12 шт.)

### Фаза 2: Repository Layer (1 день)
1. Создать `ContactRepository`
2. Создать `OCRRepository`
3. Создать `DuplicateRepository`
4. Вынести все `db.query()` из сервисов в repositories

### Фаза 3: Тестирование (1 день)
1. Unit тесты для сервисов
2. Integration тесты для endpoint'ов
3. Проверка покрытия кода

---

## 📊 Ожидаемые результаты

| Метрика | Сейчас | После миграции |
|---------|---------|----------------|
| **Макс. размер API файла** | 593 строки | < 200 строк |
| **Переиспользование логики** | Сложно | Легко |
| **Тестируемость** | Сложная | Простая |
| **Время добавления фичи** | 2-3 часа | 30-60 мин |

---

## 🎯 Пример полной структуры

```python
# API Layer (contacts.py) - только роутинг
@router.get('/')
def list_contacts(...):
    service = ContactService(db)
    return service.list_contacts(...)

# Service Layer (contact_service.py) - бизнес-логика
class ContactService:
    def list_contacts(self, ...):
        # Orchestration
        contacts = self.repo.find_all(...)
        contacts = self._apply_filters(contacts)
        return self._paginate(contacts)

# Repository Layer (contact_repository.py) - DB запросы
class ContactRepository:
    def find_all(self, filters):
        query = self.db.query(Contact)
        return self._build_query(query, filters).all()

# Model Layer (models.py) - ORM модели
class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    ...
```

---

**Дата создания:** 2025-10-22  
**Версия:** 2.22.0  
**Статус:** 🔄 В процессе миграции

