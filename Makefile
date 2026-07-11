# Makefile for FIAP STRIDE API
# Cross-platform convenience wrapper for start-api scripts

.PHONY: help start start-quick stop logs migrate test lint clean

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "FIAP STRIDE API - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start the API (build + migrations)
	@echo "🚀 Starting API..."
	@./scripts/start-api.sh

start-quick: ## Start the API quickly (skip build)
	@echo "🚀 Starting API (quick mode)..."
	@./scripts/start-api.sh --no-build

start-fg: ## Start the API in foreground mode
	@echo "🚀 Starting API (foreground mode)..."
	@./scripts/start-api.sh --foreground

stop: ## Stop all containers
	@echo "🛑 Stopping API..."
	@docker-compose down

logs: ## View API logs
	@docker-compose logs -f api

migrate: ## Run database migrations
	@echo "🔄 Running migrations..."
	@docker-compose exec api alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create msg="description")
	@docker-compose exec api alembic revision --autogenerate -m "$(msg)"

shell: ## Open shell in API container
	@docker-compose exec api /bin/bash

db-shell: ## Open PostgreSQL shell
	@docker-compose exec db psql -U postgres -d fiap_stride

test: ## Run all tests
	@echo "🧪 Running tests..."
	@docker-compose exec api pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	@docker-compose exec api pytest tests/ --cov=src --cov-report=term-missing

lint: ## Run linting (ruff + mypy)
	@echo "🔍 Running linters..."
	@ruff check src/ tests/
	@mypy src/

format: ## Format code with ruff
	@echo "📝 Formatting code..."
	@ruff format src/ tests/

clean: ## Clean up containers, volumes, and temp files
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@rm -rf storage/* logs/* __pycache__ .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.pyc" -delete 2>/dev/null || true

# Windows support (use with make -f Makefile.windows if needed)
start-windows: ## Start the API on Windows (PowerShell)
	@echo "🚀 Starting API (Windows)..."
	@powershell -ExecutionPolicy Bypass -File scripts/start-api.ps1

start-py: ## Start the API using Python script (universal)
	@echo "🚀 Starting API (Python)..."
	@python3 scripts/start-api.py
