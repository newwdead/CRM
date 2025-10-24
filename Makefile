# Makefile for FastAPI BizCard CRM
# Упрощает повседневные задачи разработки

.PHONY: help dev test lint format clean install pre-commit

# Default target
help:
	@echo "FastAPI BizCard CRM - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies and setup pre-commit"
	@echo "  make pre-commit    Setup pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  make dev           Start development environment"
	@echo "  make logs          View backend logs"
	@echo "  make shell         Open backend shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-integration  Run integration tests"
	@echo "  make test-e2e      Run E2E tests"
	@echo "  make test-cov      Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          Run linters (flake8, black check)"
	@echo "  make format        Auto-format code (black, isort)"
	@echo "  make pre-commit-run Run pre-commit on all files"
	@echo ""
	@echo "Database:"
	@echo "  make migrate       Run database migrations"
	@echo "  make db-reset      Reset database (DANGER!)"
	@echo ""
	@echo "Deployment:"
	@echo "  make build         Build Docker images"
	@echo "  make up            Start services"
	@echo "  make down          Stop services"
	@echo "  make restart       Restart services"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove cache and temp files"
	@echo "  make clean-all     Remove everything including volumes"

# Setup
install:
	pip install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

pre-commit:
	pip install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

# Development
dev:
	docker compose up -d
	@echo "✅ Development environment started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Grafana: http://localhost:3001"
	@echo "Prometheus: http://localhost:9090"

logs:
	docker compose logs -f backend

shell:
	docker compose exec backend bash

# Testing
test:
	docker compose exec backend pytest app/tests/ -v

test-unit:
	docker compose exec backend pytest app/tests/unit/ -v

test-integration:
	docker compose exec backend pytest app/tests/integration/ -v

test-e2e:
	docker compose exec backend pytest app/tests/e2e/ -v -m e2e

test-security:
	docker compose exec backend pytest app/tests/security/ -v

test-cov:
	docker compose exec backend pytest app/tests/ --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report: backend/htmlcov/index.html"

# Code Quality
lint:
	docker compose exec backend flake8 app/ --max-line-length=100
	docker compose exec backend black --check app/
	docker compose exec backend isort --check-only app/
	@echo "✅ Linting passed!"

format:
	docker compose exec backend black app/
	docker compose exec backend isort app/
	@echo "✅ Code formatted!"

pre-commit-run:
	pre-commit run --all-files

# Database
migrate:
	docker compose exec backend alembic upgrade head

db-reset:
	@echo "⚠️  WARNING: This will DELETE all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		docker compose up -d db; \
		sleep 5; \
		docker compose up -d backend; \
		echo "✅ Database reset complete!"; \
	fi

# Deployment
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart backend frontend celery-worker

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov 2>/dev/null || true
	@echo "✅ Cleaned cache and temp files!"

clean-all: clean
	docker compose down -v --remove-orphans
	@echo "✅ Cleaned everything!"

# Health checks
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq '.' || echo "Backend: DOWN"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend: UP" || echo "Frontend: DOWN"
	@curl -s http://localhost:9090/-/healthy > /dev/null && echo "Prometheus: UP" || echo "Prometheus: DOWN"
	@curl -s http://localhost:3001/api/health > /dev/null && echo "Grafana: UP" || echo "Grafana: DOWN"

# Version info
version:
	@docker compose exec backend python -c "from app.main import app; print(f'Version: {app.version}')"

