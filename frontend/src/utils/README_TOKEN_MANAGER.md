# Token Manager Documentation

## Overview

`tokenManager.js` provides a complete solution for JWT token management with automatic refresh functionality.

## Features

- ✅ **Automatic Token Refresh** - Tokens are refreshed 2 minutes before expiration
- ✅ **Token Rotation** - Implements secure token rotation strategy
- ✅ **Secure Storage** - Tokens stored in localStorage with expiration tracking
- ✅ **Auto-retry on 401** - Automatically refreshes and retries failed requests
- ✅ **Timer Management** - Efficient background refresh scheduling
- ✅ **Graceful Degradation** - Falls back to login if refresh fails

---

## Basic Usage

### 1. Initialization (App.js)

```javascript
import { initTokenManager } from './utils/tokenManager';

// In your App component's useEffect
useEffect(() => {
  initTokenManager(); // Initialize on app startup
}, []);
```

### 2. Login (Login.js)

```javascript
import { setTokens } from '../utils/tokenManager';

// After successful login
const data = await response.json();
setTokens(data.access_token, data.refresh_token, data.expires_in);
```

### 3. Logout (App.js)

```javascript
import { clearTokens } from './utils/tokenManager';

const handleLogout = () => {
  clearTokens(); // Clears tokens and cancels auto-refresh
};
```

### 4. Making Authenticated Requests

#### Option A: Using `authenticatedFetch()` (Recommended)

```javascript
import { authenticatedFetch } from '../utils/tokenManager';

// Automatic token refresh + retry on 401
const response = await authenticatedFetch('/api/contacts', {
  method: 'GET',
});
```

#### Option B: Manual Headers

```javascript
import { getAuthHeaders } from '../utils/tokenManager';

const response = await fetch('/api/contacts', {
  method: 'GET',
  headers: {
    ...getAuthHeaders(), // { Authorization: 'Bearer <token>' }
  },
});
```

---

## API Reference

### Core Functions

#### `setTokens(accessToken, refreshToken, expiresIn)`
Store tokens and schedule automatic refresh.

**Parameters:**
- `accessToken` (string) - JWT access token
- `refreshToken` (string) - JWT refresh token
- `expiresIn` (number) - Token lifetime in seconds (default: 900 = 15 min)

**Example:**
```javascript
setTokens(
  'eyJhbGciOiJIUzI1NiIs...',
  'eyJhbGciOiJIUzI1NiIs...',
  900 // 15 minutes
);
```

---

#### `getAccessToken()`
Retrieve stored access token.

**Returns:** `string | null`

**Example:**
```javascript
const token = getAccessToken();
if (token) {
  // Token exists
}
```

---

#### `getRefreshToken()`
Retrieve stored refresh token.

**Returns:** `string | null`

**Example:**
```javascript
const refreshToken = getRefreshToken();
```

---

#### `clearTokens()`
Clear all stored tokens and cancel auto-refresh timer.

**Example:**
```javascript
// On logout
clearTokens();
```

---

#### `refreshAccessToken()`
Manually refresh access token using refresh token.

**Returns:** `Promise<boolean>` - `true` if refresh successful

**Example:**
```javascript
const refreshed = await refreshAccessToken();
if (refreshed) {
  console.log('Token refreshed successfully');
}
```

---

#### `initTokenManager()`
Initialize token manager on app startup. Checks if existing tokens need refresh.

**Example:**
```javascript
useEffect(() => {
  initTokenManager();
}, []);
```

---

#### `authenticatedFetch(url, options)`
Make authenticated API request with automatic token refresh.

**Parameters:**
- `url` (string) - API endpoint
- `options` (object) - Fetch options

**Returns:** `Promise<Response>`

**Example:**
```javascript
const response = await authenticatedFetch('/api/contacts/123', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ name: 'John' }),
});

const data = await response.json();
```

---

#### `getAuthHeaders()`
Generate Authorization header with access token.

**Returns:** `Object` - Headers object

**Example:**
```javascript
const headers = {
  'Content-Type': 'application/json',
  ...getAuthHeaders(),
};
```

---

#### `needsRefresh()`
Check if access token needs refresh (expires in < 2 minutes).

**Returns:** `boolean`

**Example:**
```javascript
if (needsRefresh()) {
  await refreshAccessToken();
}
```

---

## Automatic Refresh Flow

```
1. Login
   ↓
2. setTokens(access, refresh, 900)
   ↓
3. Schedule refresh in 13 minutes (900s - 120s buffer)
   ↓
4. Timer triggers
   ↓
5. Call /api/auth/refresh with refresh token
   ↓
6. Receive new access + refresh tokens
   ↓
7. Store new tokens with setTokens()
   ↓
8. Schedule next refresh
```

---

## Security Features

### 1. Token Rotation
Every refresh generates **new** access and refresh tokens. Old tokens are invalidated.

### 2. Automatic Logout on Failure
If refresh fails with 401, user is automatically logged out and redirected to login.

### 3. Secure Storage
Tokens stored in localStorage with SHA256 hashing on backend.

### 4. Expiration Tracking
Tokens are proactively refreshed before expiration (2-minute buffer).

### 5. Request Retry
Failed 401 requests are automatically retried once after token refresh.

---

## Configuration

### Token Expiration Times (Backend)

```python
# backend/app/core/security.py
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 30    # 30 days
```

### Refresh Buffer (Frontend)

```javascript
// frontend/src/utils/tokenManager.js
const REFRESH_BUFFER_MS = 2 * 60 * 1000; // 2 minutes
```

---

## Troubleshooting

### Token Not Refreshing

**Problem:** Token expires without auto-refresh  
**Solution:** Ensure `initTokenManager()` is called on app startup

```javascript
useEffect(() => {
  initTokenManager(); // ← Make sure this runs
}, []);
```

### 401 Errors After Refresh

**Problem:** Requests fail with 401 after token refresh  
**Solution:** Use `authenticatedFetch()` instead of plain `fetch()`

```javascript
// ❌ Bad
const response = await fetch('/api/contacts');

// ✅ Good
const response = await authenticatedFetch('/api/contacts');
```

### Infinite Redirect Loop

**Problem:** App continuously redirects to login  
**Solution:** Check that refresh token is valid and not expired

```javascript
// Debug: Check token expiration
console.log('Expires at:', localStorage.getItem('token_expires_at'));
console.log('Now:', Date.now());
```

---

## Migration Guide

### From Old Token System

**Before:**
```javascript
localStorage.setItem('access_token', data.access_token);
```

**After:**
```javascript
import { setTokens } from '../utils/tokenManager';

setTokens(data.access_token, data.refresh_token, data.expires_in);
```

---

## Testing

### Manual Testing

1. **Login** - Check that tokens are stored
2. **Wait 13 minutes** - Verify auto-refresh in console
3. **Make API request** - Should work with refreshed token
4. **Logout** - Verify tokens are cleared

### Console Logs

```
Token auto-refresh scheduled in 13 minutes
Auto-refreshing access token...
Access token refreshed successfully
Token auto-refresh scheduled in 13 minutes
```

---

## Performance

- ✅ **Zero network overhead** - Refresh only when needed
- ✅ **Efficient timers** - Single timer per session
- ✅ **Minimal storage** - Only 3 localStorage keys
- ✅ **Fast lookups** - O(1) token retrieval

---

## Browser Compatibility

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ All browsers supporting `fetch()` and `localStorage`

---

**Version:** 3.5.2  
**Last Updated:** October 24, 2025  
**Author:** FastAPI BizCard CRM Team

