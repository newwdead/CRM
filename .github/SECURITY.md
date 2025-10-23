# Security Policy

## 🔒 Reporting Security Vulnerabilities

**Do not report security vulnerabilities through public GitHub issues.**

Instead, please report them responsibly by:

1. **Email:** Contact the repository maintainer directly
2. **GitHub Security Advisory:** Use GitHub's private vulnerability reporting feature

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Your contact information

We will respond within **48 hours** to acknowledge receipt.

---

## ✅ Supported Versions

| Version | Security Support |
|---------|-----------------|
| 3.4.x   | ✅ Full support |
| 3.3.x   | ✅ Full support |
| 3.2.x   | ⚠️  Critical fixes only |
| < 3.2   | ❌ Not supported |

---

## 🛡️ Security Measures

This project implements:

- JWT-based authentication
- bcrypt password hashing
- Rate limiting (API protection)
- SQL injection protection (SQLAlchemy ORM)
- XSS protection (Content Security Policy)
- HTTPS enforcement
- Security headers (OWASP recommended)
- Input validation (Pydantic)
- CORS whitelist
- File upload restrictions

---

## 📋 Security Checklist

Before deployment:

- [ ] Change all default passwords
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure CORS whitelist
- [ ] Review `.env.example` and set all variables
- [ ] Enable automated backups

See `SECURITY.md` in the root for detailed instructions.

---

## 🚀 Disclosure Policy

- We will confirm receipt within **48 hours**
- We will provide a detailed response within **7 days**
- We will release a patch within **30 days** (or less for critical issues)
- We will credit reporters (with permission) in release notes

---

## 📚 Resources

- [Full Security Documentation](../SECURITY.md)
- [Environment Variables Guide](.env.example)
- [Deployment Guide](docs/guides/setup/)

---

**Last Updated:** 2025-01-23  
**Contact:** See repository details

