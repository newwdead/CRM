# Test Coverage Improvement Plan - v3.0.1

## Current Status
**Coverage:** 39% → Target: 80%  
**Tests Status:**
- ✅ Passed: 53
- ❌ Failed: 39
- ⚠️ Errors: 46

---

## Analysis

### Current Coverage Breakdown
```
Module Type          Coverage    Target    Gap
----------------------------------------------------
Models               100%        100%      ✅ 0%
Schemas              85-100%     100%      ✅ 0-15%
Middleware           77-100%     90%       ✅ 0-13%
Core Utils           58-84%      80%       ⚠️ 0-22%
Repositories         26-68%      85%       ❌ 17-59%
Services             20-50%      85%       ❌ 35-65%
API Endpoints        11-40%      75%       ❌ 35-64%
OCR/Image Processing 6-27%       60%       ❌ 33-54%
----------------------------------------------------
TOTAL                39%         80%       ❌ 41%
```

### Priority Modules (Biggest Impact)
1. **Repositories** (26-68% → 85%) - 702 uncovered lines
2. **Services** (20-50% → 85%) - 780 uncovered lines
3. **API Endpoints** (11-40% → 75%) - 1142 uncovered lines
4. **OCR/Image Processing** (6-27% → 60%) - 415 uncovered lines

---

## Phase 1: Fix Existing Tests (v3.0.1)

### 1.1 Update Repository Tests
**File:** `app/tests/test_repositories.py`  
**Status:** 67% coverage, but 21 failed tests  
**Issue:** Tests written for old DB structure  

**Actions:**
- ✅ Fix ContactRepository tests (8 failures)
- ✅ Fix DuplicateRepository tests (3 failures)
- ✅ Fix OCRRepository tests (3 failures)
- ✅ Fix SettingsRepository tests (3 failures)
- ✅ Fix AuditRepository tests (2 failures)
- ✅ Add UserRepository tests (missing)

**Estimated Impact:** +10% coverage

### 1.2 Update Service Tests
**File:** `app/tests/test_services.py`  
**Status:** 67% coverage, but 18 failed tests  
**Issue:** Tests need to mock new repository layer  

**Actions:**
- ✅ Fix ContactService tests (15 failures)
- ✅ Add mock repositories
- ✅ Test business logic isolation

**Estimated Impact:** +5% coverage

### 1.3 Update API Tests
**Files:** `test_api_*.py`  
**Status:** Multiple errors after migration  
**Issue:** API tests expect old response formats  

**Actions:**
- ✅ Fix test_api_basic.py (1 failure)
- ✅ Fix test_api_contacts.py (18 errors)
- ✅ Fix test_api_settings.py (9 errors)
- ✅ Fix test_api_admin.py (15 errors)
- ✅ Fix test_api_ocr.py (4 errors)

**Estimated Impact:** +3% coverage

**Total Phase 1 Impact:** +18% (39% → 57%)

---

## Phase 2: Add Missing Repository Tests (v3.0.2)

### 2.1 Complete Repository Coverage
**Target:** 85% coverage for all repositories  

**ContactRepository** (currently 26%):
- ✅ Test find_by_email()
- ✅ Test find_by_phone()
- ✅ Test search_contacts()
- ✅ Test bulk_update()
- ✅ Test bulk_delete()
- ✅ Test count() with filters
- ✅ Test pagination edge cases

**UserRepository** (currently 68%):
- ✅ Test get_user_by_username()
- ✅ Test get_user_by_email()
- ✅ Test count_by_is_active()
- ✅ Test get_users_by_is_active()
- ✅ Test user deletion cascade

**DuplicateRepository** (currently 52%):
- ✅ Test get_by_contact_pair()
- ✅ Test get_pending_duplicates()
- ✅ Test update() alias
- ✅ Test duplicate status transitions

**OCRRepository** (currently 45%):
- ✅ Test get_corrections_for_contact()
- ✅ Test bulk corrections
- ✅ Test correction deletion

**SettingsRepository** (currently 42%):
- ✅ Test get_app_setting()
- ✅ Test update_app_setting()
- ✅ Test create_app_setting()
- ✅ Test get_system_settings()
- ✅ Test system setting updates

**AuditRepository** (currently 56%):
- ✅ Test get_recent_logs()
- ✅ Test get_audit_logs_by_action()
- ✅ Test get_audit_logs_by_entity()
- ✅ Test delete_old_audit_logs()

**Estimated Impact:** +15% coverage (57% → 72%)

---

## Phase 3: Add Service Layer Tests (v3.0.3)

### 3.1 ContactService Tests
**Target:** 85% coverage (currently 22%)  

**Test Coverage:**
- ✅ CRUD operations with repository mocks
- ✅ Business logic validation
- ✅ Error handling
- ✅ Transaction rollback scenarios
- ✅ Permission checking

### 3.2 DuplicateService Tests
**Target:** 85% coverage (currently 20%)  

**Test Coverage:**
- ✅ Merge contacts logic
- ✅ Mark as ignored
- ✅ Update duplicate status
- ✅ Find duplicates with threshold
- ✅ Complex merge scenarios

### 3.3 OCRService Tests
**Target:** 70% coverage (currently 26%)  

**Test Coverage:**
- ✅ OCR provider selection
- ✅ Result processing
- ✅ Confidence scoring
- ✅ Error handling

### 3.4 SettingsService Tests
**Target:** 75% coverage (currently 33%)  

**Test Coverage:**
- ✅ Setting CRUD operations
- ✅ Integration configuration
- ✅ Validation logic

**Estimated Impact:** +10% coverage (72% → 82%)

---

## Phase 4: Add API Integration Tests (v3.0.4)

### 4.1 Critical API Endpoints
**Target:** 75% coverage for all API endpoints  

**High Priority:**
- ✅ POST /auth/login - authentication flow
- ✅ GET /contacts - list with filters
- ✅ POST /contacts - create contact
- ✅ PUT /contacts/{id} - update contact
- ✅ DELETE /contacts/{id} - delete contact
- ✅ POST /ocr/upload - upload business card
- ✅ GET /duplicates - find duplicates
- ✅ POST /duplicates/merge - merge contacts
- ✅ GET /settings/system - system settings
- ✅ PUT /settings/editable - update settings

**Medium Priority:**
- GET /admin/statistics/overview
- GET /admin/audit/recent
- POST /contacts/bulk-update
- DELETE /contacts/bulk-delete
- GET /contacts/export

**Estimated Impact:** +5% coverage (82% → 87%)

---

## Implementation Strategy

### Step 1: Quick Wins (Phase 1)
**Time:** 1-2 hours  
**Target:** Fix all failing tests  
**Coverage Goal:** 39% → 57% (+18%)

### Step 2: Repository Deep Dive (Phase 2)
**Time:** 2-3 hours  
**Target:** Complete repository test suite  
**Coverage Goal:** 57% → 72% (+15%)

### Step 3: Service Layer (Phase 3)
**Time:** 2-3 hours  
**Target:** Add comprehensive service tests  
**Coverage Goal:** 72% → 82% (+10%)

### Step 4: API Integration (Phase 4)
**Time:** 1-2 hours  
**Target:** Add critical API endpoint tests  
**Coverage Goal:** 82% → 87% (+5%)

**Total Time:** 6-10 hours  
**Final Coverage:** 87% (exceeds 80% goal!)

---

## Success Metrics

### Coverage Targets by Module
```
Module                  Current   Target   Priority
-------------------------------------------------------
Models                  100%      100%     ✅ Complete
Schemas                 85-100%   100%     ✅ Complete
Middleware              77-100%   90%      🟡 Minor
UserRepository          68%       85%      🟢 High
DuplicateRepository     52%       85%      🟢 High
OCRRepository           45%       85%      🟢 High
SettingsRepository      42%       85%      🟢 High
AuditRepository         56%       85%      🟢 High
ContactRepository       26%       85%      🔴 Critical
DuplicateService        20%       85%      🔴 Critical
ContactService          22%       85%      🔴 Critical
API Endpoints           11-40%    75%      🔴 Critical
-------------------------------------------------------
OVERALL TARGET          39%       80%      🎯 GOAL
```

### Test Quality Metrics
- **Test Isolation:** All tests should use mocks/fixtures
- **Test Speed:** < 2 minutes for full suite
- **Test Reliability:** 0 flaky tests
- **Test Maintainability:** Clear naming, good documentation

---

## Benefits

### Immediate
1. ✅ Catch bugs before production
2. ✅ Validate Repository Layer migration
3. ✅ Ensure API contract stability
4. ✅ Enable confident refactoring

### Long-term
1. ✅ Faster development cycles
2. ✅ Lower bug rates in production
3. ✅ Better code documentation
4. ✅ Easier onboarding for new developers
5. ✅ Foundation for CI/CD pipeline

---

## Next Steps After 80% Coverage

1. **Performance Tests**
   - Load testing for API endpoints
   - Database query optimization
   - Response time benchmarking

2. **Security Tests**
   - Authentication testing
   - Authorization testing
   - Input validation testing
   - SQL injection prevention

3. **End-to-End Tests**
   - User workflows
   - Integration scenarios
   - Error recovery

4. **Mutation Testing**
   - Verify test quality
   - Find untested code paths
   - Improve assertion coverage

---

**Status:** Ready to execute  
**Estimated Completion:** 6-10 hours  
**Expected Final Coverage:** 87%  
**Risk Level:** Low (incremental approach)

