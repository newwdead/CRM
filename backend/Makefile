.PHONY: test test-unit test-integration coverage lint format help

help:
	@echo "Available commands:"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make lint             - Run linters (flake8, mypy)"
	@echo "  make format           - Format code with black"

test:
	pytest app/tests/ -v

test-unit:
	pytest app/tests/ -v -m unit

test-integration:
	pytest app/tests/ -v -m integration

coverage:
	pytest app/tests/ --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app/ --max-line-length=120 --exclude=migrations,__pycache__,venv
	mypy app/ --ignore-missing-imports

format:
	black app/ --line-length=120

