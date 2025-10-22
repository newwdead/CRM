# Backend Tests

**Test Coverage:** Target 80%+

---

## 📁 Test Structure

```
backend/app/tests/
├── conftest.py                   # Pytest fixtures & configuration
├── test_repositories.py          # Repository Layer tests
├── test_services.py              # Service Layer tests (NEW)
├── test_api_contacts.py          # Contacts API tests (NEW)
├── test_api_basic.py             # Basic API tests
├── test_api_admin.py             # Admin API tests
├── test_api_ocr.py               # OCR API tests
├── test_api_settings.py          # Settings API tests
├── test_duplicate_utils.py       # Duplicate detection tests
└── test_phone_utils.py           # Phone utilities tests
```

---

## 🚀 Running Tests

### All Tests
```bash
cd backend
pytest
```

### Specific Test File
```bash
pytest app/tests/test_repositories.py -v
```

### With Coverage Report
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Watch Mode (auto-run on changes)
```bash
pytest-watch
```

---

## 📊 Test Categories

### 1. Repository Tests (`test_repositories.py`)
Tests for database abstraction layer:
- CRUD operations
- Filtering & searching
- Bulk operations
- Error handling

**Coverage:** 100% (30+ tests)

### 2. Service Tests (`test_services.py`) ⭐ NEW
Tests for business logic layer:
- Service methods
- Data validation
- Business rules
- Performance

**Coverage:** 100% (25+ tests)

### 3. API Tests (`test_api_*.py`) ⭐ EXPANDED
Tests for REST API endpoints:
- Authentication
- Request/Response validation
- Error handling
- Edge cases

**Files:**
- `test_api_contacts.py` - 25+ tests ⭐ NEW
- `test_api_basic.py` - Basic endpoints
- `test_api_admin.py` - Admin endpoints
- `test_api_ocr.py` - OCR endpoints
- `test_api_settings.py` - Settings endpoints

**Coverage:** ~80%

### 4. Utility Tests
Tests for helper functions:
- `test_duplicate_utils.py` - Duplicate detection
- `test_phone_utils.py` - Phone number parsing

---

## 🛠️ Fixtures

### Database Fixtures
- `test_db` - Fresh test database for each test
- `db_session` - Alias for test_db
- `db` - Alias for compatibility

### Authentication Fixtures
- `auth_token` - JWT token for regular user
- `admin_auth_token` - JWT token for admin user

### Data Fixtures
- `test_contact` - Sample contact in DB
- `test_user_data` - Sample user data dict
- `test_contact_data` - Sample contact data dict

---

## ✅ Test Coverage Goals

| Component | Current | Target |
|-----------|---------|--------|
| Repositories | 100% | 100% ✅ |
| Services | 100% | 100% ✅ |
| API Endpoints | ~80% | 80% ✅ |
| Utilities | ~70% | 80% ⏳ |
| **Overall** | **~75%** | **80%** ⏳ |

---

## 📝 Writing New Tests

### Example Test Structure

```python
class TestMyFeature:
    """Tests for MyFeature"""
    
    def test_basic_functionality(self, db, test_contact):
        """Test basic feature"""
        # Arrange
        input_data = {"field": "value"}
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result is not None
        assert result.field == "value"
    
    def test_error_handling(self):
        """Test error cases"""
        with pytest.raises(ValueError):
            my_function(None)
```

### Best Practices

1. **Use Descriptive Names**
   ```python
   # Good
   def test_create_contact_with_valid_data(...)
   
   # Bad
   def test_contact(...)
   ```

2. **Test One Thing**
   Each test should verify one specific behavior

3. **Use Fixtures**
   Reuse common setup via fixtures

4. **Test Edge Cases**
   - Empty inputs
   - Invalid data
   - Boundary values
   - Race conditions

5. **Keep Tests Fast**
   - Use in-memory DB when possible
   - Mock external services
   - Minimize DB queries

---

## 🔧 Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Coverage Config (.coveragerc)
```ini
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

---

## 🐛 Debugging Tests

### Run with Debug Output
```bash
pytest -vv -s
```

### Run Single Test
```bash
pytest app/tests/test_services.py::TestContactService::test_create_contact -vv
```

### Drop into Debugger on Failure
```bash
pytest --pdb
```

### Show Local Variables on Failure
```bash
pytest -l
```

---

## 📈 Coverage Report

Generate HTML coverage report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## 🚨 CI/CD Integration

Tests run automatically on:
- ✅ Every push to `main`
- ✅ Every pull request
- ✅ Pre-commit hooks

See `.github/workflows/ci-cd.yml` for configuration.

---

**Created:** 2025-10-22  
**Version:** 2.31.0  
**Total Tests:** 80+  
**Coverage:** ~75% (target: 80%)

