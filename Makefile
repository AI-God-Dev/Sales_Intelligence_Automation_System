.PHONY: help install test lint format clean docker-build docker-run deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-dev: install ## Install development dependencies
	pip install black isort flake8 pylint mypy pytest pytest-cov pytest-mock

test: ## Run tests
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

lint: ## Run linters
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	pylint config utils entity_resolution
	mypy . --ignore-missing-imports

format: ## Format code
	black .
	isort .

format-check: ## Check code formatting
	black --check .
	isort --check-only .

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

docker-build: ## Build Docker image
	docker build -t sales-intelligence:latest .

docker-run: ## Run Docker container
	docker-compose up -d

docker-stop: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

deploy: ## Deploy to GCP
	chmod +x scripts/deploy_functions.sh
	./scripts/deploy_functions.sh

setup-secrets: ## Setup secrets in Secret Manager
	chmod +x scripts/setup_secrets.sh
	./scripts/setup_secrets.sh

security-check: ## Run security checks
	safety check --file requirements.txt
	bandit -r . -f json

type-check: ## Run type checking
	mypy . --ignore-missing-imports

coverage: ## Generate coverage report
	pytest tests/ --cov=. --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

