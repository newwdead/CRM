# 🔐 Authentication & Security Setup

## Overview

The FastAPI Business Card CRM includes a comprehensive JWT-based authentication system with user management, role-based access control (RBAC), and rate limiting to protect against abuse.

## Features

✅ **JWT Token Authentication**
- Secure token-based authentication
- 7-day default token expiration (configurable)
- OAuth2 Password Flow

✅ **User Management**
- User registration and login
- Admin and regular user roles
- Profile management
- User activation/deactivation

✅ **Password Security**
- Bcrypt password hashing
- Strong password requirements
- Secure password storage

✅ **Rate Limiting**
- Login: 30 attempts per minute per IP
- Registration: 10 per hour per IP
- Upload: 60 per minute per IP
- Protection against brute-force attacks

✅ **API Protection**
- All contact endpoints require authentication
- Settings endpoints require admin role
- Granular access control

## Default Admin Account

On first startup, a default admin account is created:

```
Username: admin
Password: admin
Email: admin@example.com
```

⚠️ **IMPORTANT**: Change the default password immediately after first login!

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# JWT Secret Key (CHANGE THIS!)
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars

# Token expiration (minutes, default: 10080 = 7 days)
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Default admin credentials (optional, only used if no users exist)
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin
DEFAULT_ADMIN_EMAIL=admin@example.com
```

### Generating a Secure Secret Key

```bash
# Option 1: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -hex 32
```

## API Endpoints

### Public Endpoints (No Authentication Required)

- `GET /version` - Get application version
- `GET /health` - Health check
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /ocr/providers` - Get available OCR providers
- `POST /telegram/webhook` - Telegram webhook (uses Telegram verification)

### Protected Endpoints (Authentication Required)

All endpoints below require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

#### User Profile
- `GET /auth/me` - Get current user profile
- `PUT /auth/me` - Update current user profile

#### User Management (Admin Only)
- `GET /auth/users` - List all users
- `GET /auth/users/{id}` - Get user by ID
- `DELETE /auth/users/{id}` - Delete user
- `PATCH /auth/users/{id}/admin` - Toggle admin status

#### Contacts
- `GET /contacts/` - List all contacts
- `GET /contacts/uid/{uid}` - Get contact by UID
- `POST /contacts/` - Create new contact
- `PUT /contacts/{id}` - Update contact
- `DELETE /contacts/{id}` - Delete contact

#### Import/Export
- `GET /contacts/export` - Export contacts as CSV
- `GET /contacts/export/xlsx` - Export contacts as XLSX
- `POST /contacts/import` - Import contacts from CSV/XLSX

#### Bulk Operations
- `POST /contacts/delete_bulk` - Delete multiple contacts
- `PUT /contacts/update_bulk` - Update multiple contacts

#### OCR & Upload
- `POST /upload/` - Upload and recognize business card

#### Settings (Admin Only for PUT)
- `GET /settings/telegram` - Get Telegram settings
- `PUT /settings/telegram` - Update Telegram settings (admin only)

## Usage Examples

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "full_name": "John Doe"
  }'
```

Response:
```json
{
  "id": 2,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-10-19T12:00:00Z"
}
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=SecurePassword123!"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Use Token to Access Protected Endpoints

```bash
# Store token in variable
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Get contacts
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/contacts/

# Upload business card
curl -X POST http://localhost:8000/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@business_card.jpg" \
  -F "provider=auto"

# Get current user profile
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/auth/me
```

### 4. Update User Profile

```bash
curl -X PUT http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe Jr.",
    "email": "john.doe@example.com"
  }'
```

## Frontend Integration

The frontend automatically handles authentication:

1. **Login Modal**: Click "Вход" (Login) button in the header
2. **Registration Modal**: Click "Регистрация" (Register) button
3. **Token Storage**: Tokens are stored in `localStorage`
4. **Auto-refresh**: Token is automatically included in all API requests
5. **Logout**: Click "Выход" (Logout) button to clear session

### Token Storage

Tokens are stored in the browser's localStorage:

```javascript
// Token
localStorage.getItem('access_token')

// User info
localStorage.getItem('user')
```

## Rate Limiting

Rate limits are applied per IP address:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/login` | 30 requests | 1 minute |
| `/auth/register` | 10 requests | 1 hour |
| `/upload/` | 60 requests | 1 minute |

When rate limit is exceeded, you'll receive:

```json
{
  "error": "Rate limit exceeded: 30 per 1 minute"
}
```

HTTP Status Code: `429 Too Many Requests`

## Security Best Practices

### For Production

1. **Change Secret Key**
   ```bash
   # Generate a strong secret key
   SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
   echo "SECRET_KEY=$SECRET_KEY" >> .env
   ```

2. **Change Default Admin Password**
   - Login as admin
   - Go to profile settings
   - Change password immediately

3. **Use Environment Variables**
   - Never commit `.env` file to version control
   - Keep `.env` in `.gitignore`
   - Use secure password management

4. **HTTPS Only**
   - Enable HTTPS for production
   - See `SSL_SETUP.md` for SSL configuration
   - JWT tokens should never be sent over HTTP

5. **Database Security**
   - Use strong database passwords
   - Restrict database access to backend only
   - Regular backups

6. **Rate Limiting**
   - Adjust rate limits based on your needs
   - Monitor for abuse patterns
   - Consider using Redis for distributed rate limiting

## Troubleshooting

### 401 Unauthorized

**Problem**: Getting `{"detail": "Not authenticated"}` error

**Solutions**:
1. Check that token is included in `Authorization` header
2. Verify token hasn't expired (default: 7 days)
3. Make sure token format is `Bearer <token>`
4. Login again to get a fresh token

### 403 Forbidden

**Problem**: Getting `{"detail": "Not enough permissions"}` error

**Solutions**:
1. Endpoint requires admin privileges
2. Check user's `is_admin` status
3. Contact admin to grant admin role

### 429 Too Many Requests

**Problem**: Getting rate limit exceeded error

**Solutions**:
1. Wait for the rate limit window to expire
2. Reduce request frequency
3. Contact admin if you need higher limits

### Token Expired

**Problem**: Token suddenly stops working

**Solutions**:
1. Token expired (default: 7 days)
2. Login again to get a fresh token
3. Increase `ACCESS_TOKEN_EXPIRE_MINUTES` if needed

### Cannot Login with Admin

**Problem**: `admin/admin` credentials don't work

**Solutions**:
1. Check backend logs for initialization errors
2. Verify database is running
3. Check if users were already created (admin only created if no users exist)
4. Manual admin creation:
   ```python
   from backend.app import auth_utils, database, models
   db = next(database.get_db())
   admin = auth_utils.create_user(
       db=db,
       username="admin",
       email="admin@example.com",
       password="admin",
       full_name="Administrator",
       is_admin=True
   )
   ```

## Testing Authentication

### Test Script

```bash
#!/bin/bash

# 1. Register new user
echo "1. Registering user..."
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }'

# 2. Login
echo -e "\n\n2. Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPassword123!" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"

# 3. Get profile
echo -e "\n\n3. Getting profile..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/auth/me

# 4. Get contacts
echo -e "\n\n4. Getting contacts..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/contacts/

# 5. Test rate limiting
echo -e "\n\n5. Testing rate limiting..."
for i in {1..32}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin")
  
  if [ "$STATUS" = "429" ]; then
    echo "✅ Rate limiting works! Got 429 on request $i"
    break
  fi
done

echo -e "\n\n✅ All tests completed!"
```

Save as `test_auth.sh`, make executable with `chmod +x test_auth.sh`, and run with `./test_auth.sh`.

## Database Schema

### User Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Additional Resources

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - JWT token debugger
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

## Support

If you encounter issues:

1. Check backend logs: `docker compose logs backend`
2. Verify environment variables in `.env`
3. Ensure database is running: `docker compose ps`
4. Check this documentation for common issues
5. Review backend code in `backend/app/main.py` and `backend/app/auth_utils.py`

