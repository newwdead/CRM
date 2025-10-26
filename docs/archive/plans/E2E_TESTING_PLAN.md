# 🧪 E2E Testing Plan v4.2.1

**Дата:** 24 октября 2025  
**Версия:** v4.2.1  
**Статус:** ✅ План готов

---

## 🎯 Цели E2E Testing

Протестировать critical user flows от начала до конца:
1. **User Registration & Login Flow**
2. **Business Card Upload & OCR Flow**
3. **Contact Management Flow**
4. **Duplicate Detection & Merge Flow**

---

## 📋 Critical User Flows

### Flow 1: User Registration & Authentication ⭐⭐⭐ HIGH
**Описание:** Полный цикл регистрации и аутентификации пользователя

**Steps:**
1. POST `/auth/register` - создание нового пользователя
2. GET `/auth/me` - проверка что не аутентифицирован (401)
3. POST `/auth/login` - вход с credentials
4. GET `/auth/me` - проверка что аутентифицирован
5. POST `/auth/refresh` - обновление access token
6. POST `/auth/logout` - выход

**Expected Results:**
- ✅ Пользователь создан
- ✅ JWT токены получены
- ✅ Refresh работает
- ✅ Logout очищает сессию

**Priority:** HIGH (Security critical)

---

### Flow 2: Business Card Upload & OCR ⭐⭐⭐ HIGH
**Описание:** Загрузка визитки и OCR обработка

**Steps:**
1. Login as user
2. POST `/ocr/upload` - загрузить тестовую визитку
3. Дождаться Celery обработки
4. GET `/ocr/results/{upload_id}` - получить OCR результаты
5. POST `/contacts` - создать контакт из OCR данных
6. GET `/contacts/{contact_id}` - проверить контакт

**Expected Results:**
- ✅ Визитка загружена
- ✅ OCR распознал текст
- ✅ Контакт создан с данными
- ✅ Thumbnail генерирован

**Priority:** HIGH (Core functionality)

---

### Flow 3: Contact Management ⭐⭐ MEDIUM
**Описание:** CRUD операции с контактами

**Steps:**
1. Login as user
2. GET `/contacts` - список пустой
3. POST `/contacts` - создать контакт
4. GET `/contacts` - список с 1 контактом
5. GET `/contacts/{id}` - детали контакта
6. PUT `/contacts/{id}` - обновить данные
7. GET `/contacts/{id}` - проверить обновление
8. DELETE `/contacts/{id}` - удалить
9. GET `/contacts` - список пустой

**Expected Results:**
- ✅ Контакт создаётся
- ✅ Контакт обновляется
- ✅ Контакт удаляется
- ✅ Список корректен

**Priority:** MEDIUM

---

### Flow 4: Duplicate Detection & Merge ⭐⭐ MEDIUM
**Описание:** Обнаружение и слияние дубликатов

**Steps:**
1. Login as user
2. POST `/contacts` - создать контакт A
3. POST `/contacts` - создать похожий контакт B
4. POST `/duplicates/find` - запустить поиск дубликатов
5. GET `/duplicates` - проверить найденные дубликаты
6. POST `/duplicates/{id}/merge` - слить контакты
7. GET `/contacts` - проверить что остался 1 контакт

**Expected Results:**
- ✅ Дубликаты обнаружены
- ✅ Similarity score рассчитан
- ✅ Слияние выполнено
- ✅ Данные объединены

**Priority:** MEDIUM

---

## 🛠️ Implementation Options

### Option A: pytest + httpx (Recommended) ✅
**Pros:**
- Уже установлено
- Интеграция с текущими тестами
- Быстрое выполнение
- CI/CD ready

**Cons:**
- Только API тестирование
- Нет UI тестирования

**Implementation:**
```python
# backend/app/tests/e2e/test_user_flow.py
import pytest
import httpx

@pytest.mark.e2e
async def test_complete_user_registration_flow():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Register
        response = await client.post("/auth/register", json={...})
        assert response.status_code == 201
        
        # 2. Login
        response = await client.post("/auth/login", data={...})
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # 3. Test authenticated endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 200
```

---

### Option B: Playwright (Advanced) 🎭
**Pros:**
- Full UI testing
- Real browser
- Screenshots/videos
- Cross-browser

**Cons:**
- Требует установки
- Медленнее
- Сложнее CI/CD

**Implementation:**
```python
# frontend/e2e/test_ui_flow.py
from playwright.sync_api import sync_playwright

def test_user_can_upload_business_card():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:3000/upload")
        page.set_input_files("input[type=file]", "test-card.jpg")
        page.click("button:has-text('Upload')")
        page.wait_for_selector(".ocr-results")
        assert "John Doe" in page.content()
```

---

## 📝 Recommendation

**Start with Option A (pytest + httpx):**

1. **Phase 1:** API E2E Tests (Now)
   - User registration flow
   - OCR upload flow
   - Contact CRUD flow
   - Duplicate detection flow

2. **Phase 2:** UI E2E Tests (Future)
   - Playwright for critical UI flows
   - Visual regression testing
   - Mobile responsiveness tests

---

## 🎯 Success Criteria

**Для v4.2.1:**
- ✅ 4 E2E test flows implemented
- ✅ All flows passing
- ✅ CI/CD integration
- ✅ Documentation updated

**Для v4.3.0:**
- 🔄 Playwright UI tests
- 🔄 Visual regression
- 🔄 Performance tests

---

## 📊 Current Test Coverage

| Category | Coverage | Tests |
|----------|----------|-------|
| **Unit** | 40% | 30 tests |
| **Integration** | 74% | 62 tests |
| **Security** | 65% | 252 tests |
| **E2E** | 0% | 0 tests ⚠️ |
| **Total** | 63% | 359 tests |

**After E2E implementation:**
- Total: ~70% coverage
- E2E: 4 critical flows

---

## 🚀 Implementation Steps

1. ✅ Create E2E directory structure
2. ⏳ Implement Flow 1 (Auth)
3. ⏳ Implement Flow 2 (OCR)
4. ⏳ Implement Flow 3 (CRUD)
5. ⏳ Implement Flow 4 (Duplicates)
6. ⏳ Add pytest markers
7. ⏳ Update CI/CD
8. ⏳ Documentation

---

**Prepared by:** AI Assistant  
**Date:** 24 октября 2025  
**Status:** Ready for implementation

