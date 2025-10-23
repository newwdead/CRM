# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in BizCard CRM, please report it responsibly:

### 🔒 **Please DO NOT open a public GitHub issue for security vulnerabilities**

Instead:

1. **Email:** Report to the maintainer directly
2. **Include:** 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We take security seriously and will respond within **48 hours** to all security reports.

---

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.4.x   | ✅ Yes            |
| 3.3.x   | ✅ Yes            |
| 3.2.x   | ⚠️  Security fixes only |
| 3.1.x   | ⚠️  Security fixes only |
| < 3.0   | ❌ No             |

---

## Security Features

### 🔐 Authentication & Authorization

- **JWT Tokens:** All API endpoints require authentication
- **bcrypt Password Hashing:** Passwords are hashed with bcrypt (12 rounds)
- **Token Expiration:** Configurable (default: 7 days)
- **Role-Based Access Control (RBAC):** Admin and User roles

### 🛡️ API Protection

- **Rate Limiting:** Protection against brute force and DoS attacks
  - Login: 30 requests/minute
  - Registration: 10 requests/hour
  - Upload: 60 requests/minute
  - General API: 100 requests/minute
- **Input Validation:** Pydantic schemas for all endpoints
- **SQL Injection Protection:** SQLAlchemy ORM (no raw queries)

### 🔒 Security Headers

All responses include OWASP recommended headers:

- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection`
- `Content-Security-Policy` (CSP)
- `Referrer-Policy`
- `Permissions-Policy`

### 🌐 CORS

- **Whitelist-based:** Only specific domains allowed
- **Configurable:** Set via `ALLOWED_ORIGINS` environment variable
- **Credentials:** Enabled for trusted origins only

### 📁 File Upload Security

- **Size Limit:** 20 MB per file
- **Type Validation:** Only images allowed (jpg, jpeg, png, gif, pdf)
- **Antivirus Scanning:** Recommended in production (not included)

---

## Security Best Practices

### 🔑 Environment Variables

**NEVER commit sensitive data to git!**

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

#### Required Security Variables:

```bash
# Generate strong secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
SECRET_KEY=<generated-key-here>
POSTGRES_PASSWORD=<strong-password>
LABEL_STUDIO_PASSWORD=<strong-password>
TELEGRAM_BOT_TOKEN=<your-bot-token>
WHATSAPP_VERIFY_TOKEN=<random-token>
```

### 🔒 Production Deployment

#### 1. SSL/TLS (HTTPS)

**Always use HTTPS in production!**

- Configure SSL certificates (Let's Encrypt recommended)
- Set `USE_HTTPS=true` in environment
- Configure HSTS headers (enabled by default)

#### 2. Database Security

```bash
# Use strong passwords
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Restrict database access
# In PostgreSQL: Allow only from backend container
# In docker-compose.yml: "127.0.0.1:5432:5432" (localhost only)
```

#### 3. Redis Security

```bash
# Add password authentication
redis-server --requirepass <strong-password>

# Update connection string
REDIS_URL=redis://:password@redis:6379/0
```

#### 4. Firewall Rules

```bash
# Allow only necessary ports
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw deny 8000/tcp   # Block direct backend access
ufw deny 5432/tcp   # Block direct database access
ufw enable
```

#### 5. Docker Security

```bash
# Run containers as non-root user
USER 1000:1000

# Drop unnecessary capabilities
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE  # Only if needed
```

#### 6. Dependency Scanning

```bash
# Python dependencies
pip install safety
safety check

# Node.js dependencies
npm audit
```

---

## Security Checklist

Before deploying to production:

- [ ] Strong `SECRET_KEY` generated and set
- [ ] Strong database password set
- [ ] All default passwords changed
- [ ] HTTPS/SSL configured
- [ ] CORS whitelist configured
- [ ] Rate limiting enabled
- [ ] File upload limits set
- [ ] Database backups configured
- [ ] Firewall rules configured
- [ ] Docker containers run as non-root
- [ ] Sensitive data removed from code
- [ ] `.env` file excluded from git
- [ ] Security headers enabled
- [ ] Dependencies updated
- [ ] Vulnerability scanning enabled

---

## Security Monitoring

### Logs

Monitor these logs for suspicious activity:

```bash
# Backend logs
docker logs bizcard-backend

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Failed authentication attempts
docker logs bizcard-backend | grep "authentication failed"

# Rate limit violations
docker logs bizcard-backend | grep "Rate limit exceeded"
```

### Prometheus Metrics

Access metrics at `https://yourdomain.com/metrics`:

- `http_requests_total` - Total requests
- `http_request_duration_seconds` - Request latency
- `http_requests_in_progress` - Active requests

### Alerts

Set up alerts for:

- High failed authentication rate
- Unusual API request patterns
- Database connection failures
- High memory/CPU usage

---

## Known Security Considerations

### 1. OCR Providers

- **Tesseract:** Local processing, no data leakage
- **Google Vision:** Cloud processing, data sent to Google
- **Parsio:** Cloud processing, data sent to third party

**Recommendation:** Use Tesseract for sensitive documents.

### 2. File Storage

- Uploaded files stored in `./uploads/` directory
- Files accessible via `/files/` endpoint
- **Recommendation:** Add authentication to file access in production

### 3. Telegram Integration

- Bot token must be kept secret
- Only whitelisted chats should be allowed
- **Recommendation:** Use webhook mode (not polling) in production

---

## Update Policy

- **Security patches:** Released within 48 hours of discovery
- **Critical vulnerabilities:** Released within 24 hours
- **Version support:** Latest 2 major versions

---

## Responsible Disclosure

We appreciate security researchers who:

1. Report vulnerabilities privately
2. Give us reasonable time to fix issues
3. Don't exploit vulnerabilities for malicious purposes

**Hall of Fame:** Security researchers will be acknowledged (with permission).

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

## Contact

For security concerns: See repository contact information

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 3.4.1

