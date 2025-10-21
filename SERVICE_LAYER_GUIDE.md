# 📚 Service Layer Guide - FastAPI Business Card CRM

**Версия**: v2.15+  
**Дата**: Октябрь 2025

---

## 🎯 Что такое Service Layer?

Service Layer - это архитектурный паттерн, который отделяет бизнес-логику от API endpoints и базы данных.

### **Архитектура**:

```
┌─────────────────────┐
│  API Endpoints      │  ← HTTP запросы/ответы
│  (controllers)      │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Service Layer      │  ← Бизнес-логика
│  (services)         │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Database Layer     │  ← Хранение данных
│  (models)           │
└─────────────────────┘
```

---

## 🏗️ Структура Service Layer

### **Файлы**:
```
backend/app/services/
├── __init__.py              # Экспорт всех сервисов
├── base.py                  # BaseService - базовый класс
├── contact_service.py       # ContactService
├── duplicate_service.py     # DuplicateService  
├── settings_service.py      # SettingsService
└── ocr_service.py           # OCRService
```

---

## 📝 BaseService

Все сервисы наследуются от `BaseService`:

```python
from sqlalchemy.orm import Session

class BaseService:
    """Базовый класс для всех сервисов."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # Методы управления транзакциями
    def commit(self)
    def rollback(self)
    def flush(self)
    
    # Методы работы с объектами
    def add(self, instance)
    def delete(self, instance)
    def refresh(self, instance)
```

---

## 🔧 Использование в API Endpoints

### **1. Создание dependency**

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import ContactService

def get_contact_service(db: Session = Depends(get_db)) -> ContactService:
    """Dependency для получения ContactService."""
    return ContactService(db)
```

### **2. Использование в endpoint**

```python
@router.get('/contacts/{contact_id}')
def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ContactService = Depends(get_contact_service)
):
    """Получить контакт по ID."""
    contact = service.get_by_id(contact_id)
    
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    
    return contact
```

---

## 📦 Доступные сервисы

### **1. ContactService**

**Назначение**: Управление контактами

**Методы**:
- `list_contacts()` - список с фильтрацией и пагинацией
- `search_contacts()` - быстрый поиск
- `get_by_id()` - получение по ID
- `get_by_uid()` - получение по UID
- `create_contact()` - создание контакта
- `update_contact()` - обновление контакта
- `delete_contact()` - удаление контакта
- `get_contact_history()` - история изменений

**Пример**:
```python
service = ContactService(db)

# Создание контакта
contact = service.create_contact(
    data={'full_name': 'John Doe', 'email': 'john@example.com'},
    current_user=user,
    auto_detect_duplicates=True
)

# Поиск
results = service.search_contacts(q='John', limit=10)

# Список с фильтрацией
contacts = service.list_contacts(
    q='tech',
    company='IBM',
    page=1,
    limit=20
)
```

---

### **2. DuplicateService**

**Назначение**: Обнаружение и управление дубликатами

**Методы**:
- `get_duplicates()` - список дубликатов
- `find_duplicates_manual()` - ручной поиск дубликатов
- `update_duplicate_status()` - обновление статуса
- `ignore_duplicate()` - игнорирование
- `merge_contacts()` - слияние контактов

**Пример**:
```python
service = DuplicateService(db)

# Поиск дубликатов
result = service.find_duplicates_manual(threshold=0.75)

# Получение списка
duplicates = service.get_duplicates(status='pending', limit=50)

# Слияние
result = service.merge_contacts(
    contact_id_1=1,
    contact_id_2=2,
    selected_fields={'email': 'primary', 'phone': 'secondary'},
    current_user=user
)
```

---

### **3. SettingsService**

**Назначение**: Управление системными настройками

**Методы**:
- `get_setting()` / `set_setting()` - работа с настройками
- `get_all_settings()` - все настройки
- `get_settings_dict()` - словарь настроек
- `delete_setting()` - удаление настройки
- `get_ocr_settings()` - настройки OCR
- `get_duplicate_detection_settings()` - настройки дубликатов
- `set_ocr_provider()` - установка OCR провайдера
- `set_duplicate_threshold()` - установка порога дубликатов

**Пример**:
```python
service = SettingsService(db)

# Установка настройки
service.set_setting('my_key', 'my_value')

# Получение
value = service.get_setting('my_key', default='default_value')

# OCR провайдер
service.set_ocr_provider('tesseract')

# Настройки OCR
ocr_settings = service.get_ocr_settings()
# {'provider': 'tesseract', 'language': 'eng', ...}
```

---

### **4. OCRService**

**Назначение**: Обработка изображений и OCR

**Методы**:
- `process_image()` - обработка изображения
- `extract_text()` - извлечение текста
- `scan_qr_code()` - сканирование QR
- `detect_multiple_cards()` - обнаружение нескольких карточек
- `get_ocr_blocks()` - получение блоков текста
- `save_ocr_correction()` - сохранение исправлений
- `get_available_providers()` - доступные провайдеры
- `preprocess_image()` - предобработка изображения

**Пример**:
```python
from ..ocr_providers import OCRManager

ocr_manager = OCRManager()
service = OCRService(db, ocr_manager)

# Обработка изображения
result = service.process_image(image_bytes)

# Извлечение текста
data = service.extract_text(image_bytes, provider='tesseract')

# Сканирование QR
qr_data = service.scan_qr_code(image_bytes)
```

---

## ✨ Создание нового сервиса

### **Шаг 1: Создать файл сервиса**

```python
# backend/app/services/my_service.py
from .base import BaseService
from ..models import MyModel

class MyService(BaseService):
    """
    Service for managing MyModel.
    
    Provides methods for:
    - CRUD operations
    - Business logic
    """
    
    def get_by_id(self, id: int) -> Optional[MyModel]:
        """Get model by ID."""
        return self.db.query(MyModel).filter(MyModel.id == id).first()
    
    def create(self, data: dict) -> MyModel:
        """Create new model."""
        instance = MyModel(**data)
        self.add(instance)
        self.commit()
        self.refresh(instance)
        return instance
```

### **Шаг 2: Добавить в __init__.py**

```python
# backend/app/services/__init__.py
from .my_service import MyService

__all__ = [
    ...,
    'MyService',
]
```

### **Шаг 3: Использовать в API**

```python
from ..services import MyService

def get_my_service(db: Session = Depends(get_db)) -> MyService:
    return MyService(db)

@router.get('/my-endpoint')
def my_endpoint(service: MyService = Depends(get_my_service)):
    return service.get_by_id(1)
```

---

## 🧪 Тестирование сервисов

### **Настройка тестов**:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services import ContactService

@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture
def contact_service(test_db):
    """Get ContactService instance."""
    return ContactService(test_db)
```

### **Написание тестов**:

```python
def test_create_contact(contact_service, test_user):
    """Test creating a contact."""
    contact_data = {
        'full_name': 'John Doe',
        'email': 'john@example.com'
    }
    
    contact = contact_service.create_contact(
        data=contact_data,
        current_user=test_user,
        auto_detect_duplicates=False
    )
    
    assert contact.id is not None
    assert contact.full_name == 'John Doe'
```

---

## 📊 Best Practices

### **1. Разделение ответственности**

✅ **Правильно**:
```python
# Service - бизнес-логика
class ContactService:
    def create_contact(self, data, user):
        # Format phone
        # Save to DB
        # Create audit log
        # Detect duplicates
        return contact

# Endpoint - HTTP обработка
@router.post('/contacts')
def create_contact(data, service):
    return service.create_contact(data, current_user)
```

❌ **Неправильно**:
```python
# Вся логика в endpoint
@router.post('/contacts')
def create_contact(data, db):
    # Format phone
    # Save to DB
    # Create audit log
    # Detect duplicates
    return contact
```

### **2. Обработка ошибок**

```python
class MyService(BaseService):
    def my_method(self):
        try:
            # Business logic
            self.commit()
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.rollback()
            raise
```

### **3. Транзакции**

```python
def complex_operation(self):
    try:
        # Step 1
        self.add(obj1)
        self.flush()  # Get ID without committing
        
        # Step 2
        self.add(obj2)
        
        # Commit all
        self.commit()
    except:
        self.rollback()
        raise
```

---

## 🎯 Преимущества Service Layer

1. **Переиспользование** - один сервис используется в разных endpoints
2. **Тестируемость** - легко тестировать отдельно от HTTP
3. **Читаемость** - endpoints проще и понятнее
4. **Поддержка** - изменения в одном месте
5. **Разделение** - четкая структура кода

---

## 📚 Дополнительные ресурсы

- **Release Notes**: `RELEASE_NOTES_v2.15.md`
- **Tests**: `backend/app/tests/test_services.py`
- **API Docs**: `/docs` (Swagger UI)
- **Source Code**: `backend/app/services/`

---

**Хорошего кодинга! 🚀**

