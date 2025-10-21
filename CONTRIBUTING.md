# Contributing to FastAPI Business Card CRM

Thank you for considering contributing to this project! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- Docker & Docker Compose
- PostgreSQL (for local development)
- Redis (for Celery)

### Development Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/fastapi-bizcard-crm.git
cd fastapi-bizcard-crm
```

2. **Start services with Docker Compose:**
```bash
docker compose up -d
```

3. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📋 Development Workflow

### Backend Development

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Run tests:**
```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# With coverage
make coverage
```

3. **Code quality:**
```bash
# Lint code
make lint

# Format code
make format
```

### Frontend Development

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Run development server:**
```bash
npm start
```

3. **Build for production:**
```bash
npm run build
```

## 🏗️ Project Structure

```
fastapi-bizcard-crm/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints (modular)
│   │   ├── core/         # Config, security, utils
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── tests/        # Pytest tests
│   │   └── main.py       # FastAPI app
│   ├── requirements.txt
│   └── Makefile
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   └── translations/ # i18n files
│   └── package.json
└── docker-compose.yml
```

## 📝 Coding Standards

### Python (Backend)

- **Style:** PEP 8, formatted with `black`
- **Line length:** 120 characters
- **Type hints:** Use where appropriate
- **Docstrings:** Google style for public functions
- **Testing:** Write tests for all new features

**Example:**
```python
def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity score between two texts.
    
    Args:
        text1: First text string
        text2: Second text string
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Implementation
    pass
```

### JavaScript (Frontend)

- **Style:** ES6+, formatted with Prettier
- **Components:** Functional components with hooks
- **Props:** Destructure in function parameters
- **Styling:** Tailwind CSS utility classes
- **Comments:** JSDoc for complex functions

**Example:**
```javascript
/**
 * Format phone number to standard format
 * @param {string} phone - Raw phone number
 * @returns {string} Formatted phone number
 */
const formatPhone = (phone) => {
  // Implementation
};
```

## 🧪 Testing Guidelines

### Unit Tests

- Test individual functions and utilities
- Mock external dependencies
- Use descriptive test names
- Aim for 80%+ coverage

```python
def test_phone_formatting_russian_number():
    """Test formatting Russian phone number"""
    assert format_phone_number("79001234567") == "+7 (900) 123-45-67"
```

### Integration Tests

- Test API endpoints
- Test database operations
- Test authentication flows
- Use test fixtures

```python
def test_create_contact_authenticated(client, auth_token):
    """Test creating contact with valid auth"""
    response = client.post(
        "/contacts/",
        json={"full_name": "Test User"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
```

## 🔀 Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Messages

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Example:**
```
feat(contacts): add duplicate detection

- Implement fuzzy matching algorithm
- Add similarity threshold configuration
- Create duplicate merge UI

Closes #123
```

### Pull Request Process

1. **Create feature branch:**
```bash
git checkout -b feature/my-feature
```

2. **Make changes and commit:**
```bash
git add .
git commit -m "feat: add my feature"
```

3. **Push and create PR:**
```bash
git push origin feature/my-feature
```

4. **PR Requirements:**
   - ✅ All tests pass
   - ✅ Code review approved
   - ✅ No linter errors
   - ✅ Documentation updated
   - ✅ CHANGELOG updated (if applicable)

## 🐛 Reporting Bugs

When reporting bugs, please include:

- **Description:** Clear description of the issue
- **Steps to reproduce:** Detailed steps
- **Expected behavior:** What should happen
- **Actual behavior:** What actually happens
- **Environment:** OS, Python/Node version, browser
- **Screenshots:** If applicable
- **Logs:** Relevant error messages

## 💡 Feature Requests

When requesting features, please include:

- **Problem:** What problem does this solve?
- **Solution:** Proposed solution
- **Alternatives:** Any alternatives considered
- **Additional context:** Screenshots, examples

## 📚 Documentation

- Update README.md for major changes
- Update API docs (docstrings)
- Create ADR for architectural decisions
- Update CHANGELOG.md for releases

## 🎯 Code Review Checklist

**Before submitting PR:**
- [ ] Tests pass locally
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No sensitive data committed
- [ ] Changelog updated (if needed)

**For reviewers:**
- [ ] Code is readable and maintainable
- [ ] Tests cover new functionality
- [ ] No obvious bugs or security issues
- [ ] Performance implications considered
- [ ] Documentation is clear

## 📞 Getting Help

- **Issues:** Open an issue on GitHub
- **Discussions:** Use GitHub Discussions
- **Documentation:** Check `/docs` folder
- **Code of Conduct:** Be respectful and professional

## 📄 License

By contributing, you agree that your contributions will be licensed under the project's license.

---

Thank you for contributing! 🎉

