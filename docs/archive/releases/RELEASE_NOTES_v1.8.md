# 🔐 Release Notes v1.8 - Security & Authentication

**Release Date:** October 19, 2025  
**Version:** 1.8.0

---

## 🎯 Overview

Version 1.8 introduces a complete **authentication and security system** to the BizCard CRM, implementing JWT-based user authentication, role-based access control, and API rate limiting. All data operations now require user authentication, ensuring data privacy and security.

---

## ✨ New Features

### 🔐 JWT Authentication System

- **Token-based authentication** using industry-standard JWT (JSON Web Tokens)
- **Secure password hashing** with bcrypt
- **7-day default token expiration** (configurable via environment variables)
- **OAuth2 Password Flow** for standard compliance
- **Automatic token refresh** and validation

### 👥 User Management

- **User Registration**
  - Username validation (alphanumeric, 3-50 characters)
  - Email validation and uniqueness checks
  - Strong password requirements
  - Full name support
  
- **User Login**
  - Login with username or email
  - Secure password verification
  - JWT token generation
  - Failed login tracking

- **User Profiles**
  - View and edit own profile
  - Update email, full name, and password
  - Profile information display in UI

- **Admin Features**
  - User list and management
  - View user details
  - Delete users
  - Toggle admin privileges
  - System-wide settings access

### 🛡️ Role-Based Access Control (RBAC)

**Admin Role:**
- Full access to all features
- User management (create, read, update, delete)
- System settings configuration
- Telegram bot configuration
- OCR provider management

**Regular User Role:**
- Contact management (CRUD operations)
- Upload and OCR business cards
- Import/Export contacts
- View own profile
- Update own profile

### 🚫 API Protection

All endpoints now require authentication except:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login  
- `GET /version` - Application version
- `GET /health` - Health check
- `GET /ocr/providers` - OCR provider information
- `POST /telegram/webhook` - Telegram webhook (uses Telegram verification)

**Protected Endpoints:**
- All `/contacts/*` endpoints
- `/upload/` endpoint
- `/settings/*` endpoints
- `/auth/me` and `/auth/users` endpoints

### ⏱️ Rate Limiting

Intelligent rate limiting to prevent abuse:

| Endpoint | Limit | Window | Purpose |
|----------|-------|--------|---------|
| `/auth/login` | 30 requests | 1 minute | Prevent brute-force attacks |
| `/auth/register` | 10 requests | 1 hour | Prevent spam registrations |
| `/upload/` | 60 requests | 1 minute | Protect OCR resources |

Rate limit exceeded returns HTTP 429 with retry information.

### 🖥️ Frontend Integration

- **Login Modal**
  - Sleek modal design
  - Username/password input
  - Remember me (token storage)
  - Error handling with visual feedback
  - Switch to registration

- **Registration Modal**
  - Full registration form
  - Field validation
  - Password confirmation
  - Real-time error messages
  - Auto-login after registration

- **Header Authentication UI**
  - User badge showing role (Admin/User)
  - Username display
  - Login/Register buttons for guests
  - Logout button for authenticated users
  - Welcome message on home page

- **Token Management**
  - Automatic token storage in localStorage
  - Token validation on app load
  - Auto-redirect on expired tokens
  - Secure token transmission in headers

### 📚 Documentation

New comprehensive documentation:

**AUTH_SETUP.md** includes:
- Complete authentication overview
- Default admin credentials
- Environment variable configuration
- API endpoint documentation
- Usage examples (curl, frontend)
- Rate limiting details
- Security best practices
- Troubleshooting guide
- Testing scripts

---

## 🔧 Technical Details

### Backend Changes

**New Dependencies:**
- `python-jose[cryptography]` - JWT token handling
- `passlib==1.7.4` - Password hashing
- `bcrypt==4.0.1` - Bcrypt algorithm
- `slowapi` - Rate limiting middleware

**New Files:**
- `backend/app/auth_utils.py` - Authentication utilities
- `backend/app/schemas.py` - Pydantic schemas for auth

**Database Schema:**
- New `users` table with fields:
  - `id` (primary key)
  - `username` (unique)
  - `email` (unique)
  - `hashed_password`
  - `full_name`
  - `is_active` (boolean)
  - `is_admin` (boolean)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)

### Frontend Changes

**New Components:**
- `frontend/src/components/Login.js` - Login modal
- `frontend/src/components/Register.js` - Registration modal

**Updated Components:**
- `frontend/src/App.js` - Authentication state management
- `frontend/src/index.css` - Auth UI styles

**State Management:**
- User state tracking
- Token storage and validation
- Auth modals visibility
- Loading states for async operations

### API Endpoints

**New Endpoints:**
```
POST   /auth/register          - Register new user
POST   /auth/login             - Login and get token
GET    /auth/me                - Get current user profile
PUT    /auth/me                - Update current user profile
GET    /auth/users             - List all users (admin)
GET    /auth/users/{id}        - Get user by ID (admin)
DELETE /auth/users/{id}        - Delete user (admin)
PATCH  /auth/users/{id}/admin  - Toggle admin status (admin)
```

**Protected Endpoints:**
All existing endpoints now require `Authorization: Bearer <token>` header.

---

## 🚀 Migration Guide

### For Existing Installations

1. **Pull Latest Code:**
   ```bash
   git pull origin main
   ```

2. **Update .env (Optional but Recommended):**
   ```bash
   # Add to your .env file
   SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
   ACCESS_TOKEN_EXPIRE_MINUTES=10080
   DEFAULT_ADMIN_USERNAME=admin
   DEFAULT_ADMIN_PASSWORD=admin
   ```

3. **Rebuild and Restart:**
   ```bash
   docker compose down
   docker compose up -d --build
   ```

4. **Default Admin Created:**
   - On first startup with no existing users, admin/admin is created
   - If you already have users, they are preserved
   - Login with admin/admin or create a new user

5. **Change Default Password:**
   - Login as admin
   - Click on username in header
   - Update profile and change password

### For New Installations

Follow the normal installation process in README.md. The default admin account will be created automatically.

---

## 🔒 Security Recommendations

### Production Deployment

1. **Generate Strong Secret Key:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Add to `.env`:
   ```
   SECRET_KEY=<generated-key-here>
   ```

2. **Change Default Admin Password:**
   - Immediately after first login
   - Use a strong, unique password
   - Consider using a password manager

3. **Configure Token Expiration:**
   ```bash
   # Shorter expiration for sensitive environments
   ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 1 day
   ```

4. **Enable HTTPS:**
   - Required for production
   - See `SSL_SETUP.md` for configuration
   - Never send JWT tokens over HTTP

5. **Database Security:**
   - Use strong database passwords
   - Restrict database access
   - Regular backups

6. **Rate Limiting:**
   - Monitor rate limit hits
   - Adjust limits based on usage patterns
   - Consider Redis for distributed systems

7. **Environment Variables:**
   - Never commit `.env` to version control
   - Use secrets management in production
   - Rotate secrets regularly

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Test registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'

# 2. Test login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPass123!" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/contacts/

# 4. Test rate limiting
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=wrong"
done
```

### Automated Testing

See `AUTH_SETUP.md` for a complete test script.

---

## 📊 Performance Impact

- **Minimal overhead:** JWT validation is fast (~1ms per request)
- **Database queries:** Additional user lookup on authenticated requests
- **Rate limiting:** In-memory tracking with negligible impact
- **Token size:** ~200-300 bytes per token

---

## 🐛 Bug Fixes

- Fixed bcrypt compatibility issues with passlib
- Resolved frontend CORS issues with auth headers
- Fixed token expiration validation
- Corrected rate limiting configuration

---

## ⬆️ Upgrade from v1.7

### Breaking Changes

⚠️ **All API endpoints now require authentication** except public ones listed above.

**Impact:**
- External scripts and integrations must now include JWT tokens
- Telegram webhook still works (uses Telegram verification)
- Health checks and version endpoints remain public

**Migration:**
1. Update API clients to obtain and use JWT tokens
2. Create service accounts for automated scripts
3. Update documentation for third-party integrations

### Backward Compatibility

- Existing contacts data is preserved
- Settings and configurations remain intact
- Telegram integration continues to work
- No changes to database schema for existing tables

---

## 🎁 Additional Improvements

- Enhanced error messages for authentication failures
- Improved logging for security events
- Better validation messages in registration
- Cleaner UI for auth modals
- Updated API documentation with auth examples

---

## 📖 Documentation Updates

- **NEW:** `AUTH_SETUP.md` - Complete authentication guide
- **Updated:** `README.md` - Added security features
- **Updated:** `README.ru.md` - Russian translation
- **Updated:** Project structure documentation

---

## 🙏 Acknowledgments

This release implements industry-standard security practices following:
- OWASP Authentication Guidelines
- FastAPI Security Best Practices
- JWT.io Recommendations

---

## 📞 Support

- **Documentation:** See `AUTH_SETUP.md` for detailed guides
- **Issues:** Report on GitHub Issues
- **Questions:** Check documentation first, then open a discussion

---

## 🗺️ Roadmap for v1.9

Potential features for next release:
- Email verification for registration
- Password reset flow
- Two-factor authentication (2FA)
- OAuth2 social login (Google, GitHub)
- API key authentication for service accounts
- Audit logging for security events
- Session management and revocation
- IP whitelisting

---

**Thank you for using BizCard CRM!** 🚀

Stay secure! 🔐

