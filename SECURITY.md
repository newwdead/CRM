# Security Policy

## 🔒 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 5.0.x   | :white_check_mark: |
| 4.x.x   | :x:                |
| < 4.0   | :x:                |

## 🐛 Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Email:** security@ibbase.ru

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Expected Response Time:**
- Initial response: 48 hours
- Status update: 5 business days
- Fix timeline: Depends on severity

### Severity Levels

| Severity | Response Time | Examples |
|----------|---------------|----------|
| **Critical** | 24 hours | RCE, SQL Injection, Authentication bypass |
| **High** | 72 hours | XSS, CSRF, Privilege escalation |
| **Medium** | 1 week | Information disclosure, DoS |
| **Low** | 2 weeks | Minor security improvements |

## 🛡️ Security Measures

### Implemented

- ✅ JWT Authentication with refresh tokens
- ✅ Two-Factor Authentication (2FA)
- ✅ Password hashing (bcrypt)
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ Input validation (Pydantic)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ File upload validation
- ✅ HTTPS/TLS in production
- ✅ Security headers
- ✅ Dependency scanning (Dependabot)
- ✅ Code scanning (CodeQL)

### Security Headers

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

## 🔍 Security Audits

- **Last Audit:** 2025-10-25
- **Security Score:** 85/100 (Excellent)
- **Critical Issues:** 0
- **High Issues:** 0
- **Medium Issues:** 0

## 📚 Security Documentation

- [Security Audit Report](SECURITY_AUDIT_v5.0.3.md)
- [Security Fixes Plan](SECURITY_FIXES_PLAN_v5.0.3.md)

## 🔗 External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security](https://github.com/newwdead/CRM/security)
- [Dependabot Alerts](https://github.com/newwdead/CRM/security/dependabot)

## ⚠️ Known Issues

Currently, there are no known security issues.

Last updated: 2025-10-25
