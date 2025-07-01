.PHONY: help build run dev dev-rebuild dev-background dev-logs test test-docker clean logs shell stop install format lint fix check build-prod run-prod dev-prod logs-prod shell-prod stop-prod clean-prod

# Variables
DOCKER_DEV_COMPOSE := docker/development/docker-compose.yml
DOCKER_PROD_COMPOSE := docker/production/docker-compose.yml
DATA_DIR := data/scraping_results

# Ensure data directory exists
$(DATA_DIR):
	@mkdir -p $(DATA_DIR)

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "🐳 Development Commands:"
	@echo "  dev            - Run in development mode with 2FA support"
	@echo "  dev-rebuild    - Force rebuild and run in development mode"
	@echo "  dev-background - Run in background"
	@echo "  dev-logs       - Run with log output only"
	@echo "  test-docker    - Run tests in Docker"
	@echo "  test-permissions - Run Docker permission tests"
	@echo "  logs           - Show container logs"
	@echo "  shell          - Open shell in container"
	@echo "  stop           - Stop running containers"
	@echo "  clean          - Remove Docker images and containers"
	@echo ""
	@echo "🚀 Production Commands:"
	@echo "  build-prod     - Build production image"
	@echo "  run-prod       - Run in production mode"
	@echo "  logs-prod      - Show production logs"
	@echo "  shell-prod     - Open production shell"
	@echo "  stop-prod      - Stop production containers"
	@echo "  clean-prod     - Clean production environment"
	@echo ""
	@echo "🧪 Local Development:"
	@echo "  install        - Install dependencies"
	@echo "  test           - Run tests locally"
	@echo "  format         - Format code with Ruff"
	@echo "  lint           - Run linter"
	@echo "  fix            - Auto-fix code issues"
	@echo "  check          - Run lint + test"

# ====================
# Development Environment
# ====================

build: $(DATA_DIR)
	docker-compose -f $(DOCKER_DEV_COMPOSE) build

run: $(DATA_DIR)
	docker-compose -f $(DOCKER_DEV_COMPOSE) up --build tor-scraper

dev: $(DATA_DIR)
	docker-compose -f $(DOCKER_DEV_COMPOSE) --profile dev run --rm tor-scraper-dev

dev-rebuild: $(DATA_DIR)
	docker-compose -f $(DOCKER_DEV_COMPOSE) --profile dev run --rm --build tor-scraper-dev

dev-background:
	docker-compose -f $(DOCKER_DEV_COMPOSE) --profile dev up -d tor-scraper-dev

dev-logs:
	docker-compose -f $(DOCKER_DEV_COMPOSE) --profile dev up tor-scraper-dev

test-docker: $(DATA_DIR)
	docker-compose -f $(DOCKER_DEV_COMPOSE) --profile test up --build tor-scraper-test

test-permissions: $(DATA_DIR)
	docker-compose -f $(DOCKER_DEV_COMPOSE) --profile dev run --rm tor-scraper-test pytest tests/test_docker_file_permissions.py -v

logs:
	docker-compose -f $(DOCKER_DEV_COMPOSE) logs -f

shell:
	docker-compose -f $(DOCKER_DEV_COMPOSE) exec tor-scraper /bin/bash

stop:
	docker-compose -f $(DOCKER_DEV_COMPOSE) down

clean:
	docker-compose -f $(DOCKER_DEV_COMPOSE) down --rmi all --volumes --remove-orphans
	docker system prune -f

# ====================
# Production Environment
# ====================

build-prod:
	docker-compose -f $(DOCKER_PROD_COMPOSE) build

run-prod:
	docker-compose -f $(DOCKER_PROD_COMPOSE) up --build tor-scraper

logs-prod:
	docker-compose -f $(DOCKER_PROD_COMPOSE) logs -f

shell-prod:
	docker-compose -f $(DOCKER_PROD_COMPOSE) exec tor-scraper /bin/bash

stop-prod:
	docker-compose -f $(DOCKER_PROD_COMPOSE) down

clean-prod:
	docker-compose -f $(DOCKER_PROD_COMPOSE) down --rmi all --volumes --remove-orphans

# ====================
# Local Development
# ====================

test:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

install:
	uv sync --all-extras

dev-install:
	uv sync --extra dev --extra selenium

format:
	uv run ruff format src tests

lint:
	uv run ruff check src tests

fix:
	uv run ruff check --fix src tests

check: lint test

update:
	uv lock --upgrade
	uv sync --all-extras

clean-local:
	rm -rf .pytest_cache htmlcov .coverage .ruff_cache __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ====================
# Utility Commands
# ====================

railway-info:
	@echo "🚂 Railway Deployment:"
	@echo "1. Connect GitHub repository to Railway"
	@echo "2. Set environment variables:"
	@echo "   - TBB_PATH=/opt/torbrowser/tor-browser"
	@echo "   - DISPLAY=:99"
	@echo "   - PYTHONPATH=/app"
	@echo "3. Automatic deployment starts"

# Local development without Docker
dev-local: $(DATA_DIR)
	uv run python src/main.py

# Watch files for changes (requires entr)
watch:
	find src tests -name "*.py" | entr -r make test

# Generate requirements.txt for compatibility
requirements:
	uv pip compile pyproject.toml -o requirements.txt
