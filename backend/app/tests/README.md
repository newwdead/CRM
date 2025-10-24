# 🧪 Test Suite Organization

Organized test suite for FastAPI Business Card CRM backend.

## 📂 Structure

```
tests/
├── README.md            # This file
├── conftest.py          # Shared fixtures and configuration
├── __init__.py
├── unit/                # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_phone_utils.py
│   └── test_duplicate_utils.py
├── integration/         # Integration tests (DB, services)
│   ├── __init__.py
│   ├── test_api_admin.py
│   ├── test_api_basic.py
│   ├── test_api_contacts.py
│   ├── test_api_ocr.py
│   ├── test_api_settings.py
│   ├── test_repositories.py
│   └── test_services.py
└── security/            # Security tests (auth, vulnerabilities)
    ├── __init__.py
    ├── test_file_security.py
    ├── test_refresh_tokens.py
    ├── test_security_auth.py
    ├── test_security_dependencies.py
    ├── test_security_headers.py
    ├── test_security_jwt.py
    ├── test_security_passwords.py
    └── test_two_factor.py
```

## 📊 Test Categories

### 🔹 Unit Tests (2 tests)
**Location:** `unit/`  
**Purpose:** Fast, isolated tests for individual functions and utilities.  
**Run:** `pytest app/tests/unit -m unit`

- `test_phone_utils.py` - Phone number formatting and validation
- `test_duplicate_utils.py` - Duplicate detection algorithms

### 🔹 Integration Tests (7 tests)
**Location:** `integration/`  
**Purpose:** Tests that verify interaction between components (API, DB, services).  
**Run:** `pytest app/tests/integration -m integration`

- `test_api_admin.py` - Admin API endpoints
- `test_api_basic.py` - Basic API functionality
- `test_api_contacts.py` - Contact management API
- `test_api_ocr.py` - OCR processing API
- `test_api_settings.py` - Settings API
- `test_repositories.py` - Repository layer tests
- `test_services.py` - Service layer tests

### 🔹 Security Tests (8 tests)
**Location:** `security/`  
**Purpose:** Security-focused tests (auth, permissions, vulnerabilities).  
**Run:** `pytest app/tests/security -m security`

- `test_file_security.py` - File upload security
- `test_refresh_tokens.py` - JWT refresh token security
- `test_security_auth.py` - Authentication security
- `test_security_dependencies.py` - Dependency security scanning
- `test_security_headers.py` - HTTP security headers
- `test_security_jwt.py` - JWT token security
- `test_security_passwords.py` - Password hashing and validation
- `test_two_factor.py` - 2FA implementation security

## 🚀 Running Tests

### Run all tests
```bash
pytest
```

### Run specific category
```bash
pytest app/tests/unit              # Unit tests only
pytest app/tests/integration       # Integration tests only
pytest app/tests/security          # Security tests only
```

### Run with markers (coming soon)
```bash
pytest -m unit                     # All unit tests
pytest -m integration              # All integration tests
pytest -m security                 # All security tests
pytest -m "not integration"        # Skip integration tests
```

### Run specific file
```bash
pytest app/tests/unit/test_phone_utils.py
pytest app/tests/security/test_two_factor.py
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

## 📈 Test Statistics

**Total Tests:** 17  
**Coverage:** ~86.5% (115/133 tests passing)

| Category    | Count | Purpose                          |
|-------------|-------|----------------------------------|
| Unit        | 2     | Fast, isolated function tests    |
| Integration | 7     | API, DB, service integration     |
| Security    | 8     | Auth, permissions, vulnerabilities|

## 🎯 Best Practices

1. **Unit Tests:** Should be fast (<1s) and not require external dependencies
2. **Integration Tests:** Can use database, but should use test fixtures
3. **Security Tests:** Focus on authentication, authorization, and vulnerability scanning
4. **Fixtures:** Shared fixtures in `conftest.py`
5. **Naming:** Always prefix test files with `test_`
6. **Assertions:** Use descriptive assertion messages

## 📝 Adding New Tests

### Unit Test Example
```python
# tests/unit/test_my_util.py
def test_my_function():
    result = my_function("input")
    assert result == "expected"
```

### Integration Test Example
```python
# tests/integration/test_my_api.py
def test_api_endpoint(client, db_session):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

### Security Test Example
```python
# tests/security/test_my_security.py
def test_unauthorized_access(client):
    response = client.get("/api/protected")
    assert response.status_code == 401
```

---

## 🔗 Related Documentation

- [Main README](../../../../README.md)
- [Backend 3-Layer Pattern](../../BACKEND_3_LAYER_PATTERN.md)
- [Security Documentation](../../../../SECURITY.md)

---

*Last Updated: 2025-10-24 (v3.7.x - Phase 3)*
