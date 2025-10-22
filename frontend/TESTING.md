# 🧪 Frontend Testing Guide

**Version:** 2.30.0  
**Date:** 2025-10-22  
**Status:** ✅ Implemented

---

## 📋 Overview

Comprehensive testing setup for React frontend using Jest and React Testing Library.

**Test Types:**
- **Unit Tests** - Components, hooks, utilities
- **Integration Tests** - Module interactions
- **E2E Tests** - User workflows (future)

---

## 🛠️ Tech Stack

- **Jest** - Test runner
- **React Testing Library** - Component testing
- **@testing-library/react-hooks** - Hook testing
- **jest-dom** - DOM matchers

---

## 📁 Project Structure

```
frontend/src/
├── __tests__/
│   ├── components/           # Component tests
│   │   └── ErrorBoundary.test.js
│   ├── hooks/                # Hook tests
│   │   └── useDuplicates.test.js
│   └── utils/                # Utility tests
│       └── preloadComponents.test.js
├── setupTests.js             # Test configuration
└── ...
```

---

## 🚀 Running Tests

### All Tests
```bash
npm test
```

### Watch Mode
```bash
npm test -- --watch
```

### Coverage Report
```bash
npm test -- --coverage
```

### Specific Test File
```bash
npm test -- ErrorBoundary
```

### Update Snapshots
```bash
npm test -- -u
```

---

## ✍️ Writing Tests

### Component Tests

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  test('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  test('handles click', () => {
    const handleClick = jest.fn();
    render(<MyComponent onClick={handleClick} />);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

### Hook Tests

```javascript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useMyHook } from '../useMyHook';

describe('useMyHook', () => {
  test('returns initial state', () => {
    const { result } = renderHook(() => useMyHook());
    
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  test('fetches data', async () => {
    const { result } = renderHook(() => useMyHook());
    
    await act(async () => {
      await result.current.fetchData();
    });
    
    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });
  });
});
```

### Utility Tests

```javascript
import { myUtility } from '../myUtility';

describe('myUtility', () => {
  test('returns correct value', () => {
    const result = myUtility(input);
    expect(result).toBe(expected);
  });

  test('handles edge cases', () => {
    expect(myUtility(null)).toBeNull();
    expect(myUtility(undefined)).toBeUndefined();
  });
});
```

---

## 🎯 Test Coverage

### Current Coverage

| Category | Files | Coverage |
|----------|-------|----------|
| Components | ErrorBoundary | ✅ 100% |
| Hooks | useDuplicates | ✅ 100% |
| Utils | preloadComponents | ✅ 100% |

### Coverage Goals

- **Components:** 70%
- **Hooks:** 80%
- **Utils:** 90%
- **Overall:** 70%

---

## 🧩 Test Examples

### 1. ErrorBoundary Tests

**File:** `__tests__/components/ErrorBoundary.test.js`

**Coverage:**
- ✅ Renders children without errors
- ✅ Shows error UI when error occurs
- ✅ Displays error icon and buttons
- ✅ Resets error state on retry
- ✅ Shows error details in dev mode
- ✅ Increments error count
- ✅ Navigates home on button click

**Stats:** 10 tests, 100% coverage

---

### 2. preloadComponents Tests

**File:** `__tests__/utils/preloadComponents.test.js`

**Coverage:**
- ✅ preloadComponent() with cached component
- ✅ preloadComponent() with uncached component
- ✅ preloadComponents() multiple components
- ✅ preloadOnHover() returns function
- ✅ preloadOnIdle() uses requestIdleCallback
- ✅ preloadOnIdle() fallback to setTimeout
- ✅ preloadAfterDelay() with default delay
- ✅ preloadAfterDelay() with custom delay

**Stats:** 11 tests, 100% coverage

---

### 3. useDuplicates Hook Tests

**File:** `__tests__/hooks/useDuplicates.test.js`

**Coverage:**
- ✅ Loads duplicates on mount
- ✅ Handles loading state
- ✅ Handles errors
- ✅ Merges duplicates
- ✅ Handles merge errors
- ✅ Marks as reviewed
- ✅ Dismisses duplicate
- ✅ Manual reload
- ✅ Language support

**Stats:** 9 tests, 100% coverage

---

## 🔧 Mocking

### API Mocks

```javascript
jest.mock('../api/myApi', () => ({
  fetchData: jest.fn(() => Promise.resolve({ data: [] })),
  saveData: jest.fn(() => Promise.resolve({ success: true })),
}));
```

### React Router Mocks

```javascript
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useParams: () => ({ id: '1' }),
}));
```

### LocalStorage Mocks

```javascript
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;
```

### Toast Mocks

```javascript
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
}));
```

---

## 📊 Best Practices

### DO:
- ✅ Test user interactions, not implementation
- ✅ Use semantic queries (getByRole, getByText)
- ✅ Test error states
- ✅ Test loading states
- ✅ Mock external dependencies
- ✅ Keep tests isolated
- ✅ Use descriptive test names

### DON'T:
- ❌ Test implementation details
- ❌ Use `container.querySelector()`
- ❌ Test third-party libraries
- ❌ Share state between tests
- ❌ Ignore async operations
- ❌ Over-mock (mock only what's needed)

---

## 🐛 Debugging Tests

### Run Single Test
```bash
npm test -- -t "renders correctly"
```

### Debug Mode
```javascript
import { screen, debug } from '@testing-library/react';

test('my test', () => {
  render(<MyComponent />);
  debug(); // Prints DOM tree
});
```

### Watch for Changes
```bash
npm test -- --watch
```

### Verbose Output
```bash
npm test -- --verbose
```

---

## 📈 Coverage Report

### Generate Report
```bash
npm test -- --coverage --watchAll=false
```

### View HTML Report
```bash
open coverage/lcov-report/index.html
```

### Coverage Thresholds

```json
{
  "jest": {
    "coverageThresholds": {
      "global": {
        "branches": 70,
        "functions": 70,
        "lines": 70,
        "statements": 70
      }
    }
  }
}
```

---

## 🔄 Continuous Integration

### GitHub Actions

```yaml
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm test -- --coverage --watchAll=false
```

---

## 📚 Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/react)
- [Testing Hooks](https://react-hooks-testing-library.com/)
- [jest-dom Matchers](https://github.com/testing-library/jest-dom)

---

## 🎯 Next Steps

### Immediate:
1. ⏳ Add more component tests
2. ⏳ Add module hook tests (OCR, Services, Contacts)
3. ⏳ Increase coverage to 70%

### Short-term:
4. ⏳ Integration tests
5. ⏳ E2E tests with Cypress/Playwright
6. ⏳ Visual regression tests

### Long-term:
7. ⏳ Performance testing
8. ⏳ Accessibility testing
9. ⏳ Security testing

---

**Created:** 2025-10-22  
**Version:** 2.30.0  
**Status:** ✅ Production Ready

**Test Stats:**
- Files: 3
- Tests: 30+
- Coverage: 100% (for tested files)
- Target: 70% overall

