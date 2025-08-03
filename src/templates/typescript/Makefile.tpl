# {{SERVICE_NAME}} Makefile
.PHONY: help install dev build test lint format clean check

# Colors for output
GREEN := \033[0;32m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show available commands
	@echo "$(BLUE){{SERVICE_NAME}} - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@npm install
	@echo "$(GREEN)Dependencies installed!$(NC)"

dev: ## Start development server with auto-reload
	@echo "$(BLUE)Starting development server...$(NC)"
	@npm run dev

build: ## Build the application
	@echo "$(BLUE)Building application...$(NC)"
	@npm run build
	@echo "$(GREEN)Build complete!$(NC)"

start: ## Start production server
	@echo "$(BLUE)Starting production server...$(NC)"
	@npm start

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@npm test

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@npm run test:watch

lint: ## Run linting
	@echo "$(BLUE)Running linters...$(NC)"
	@npm run lint

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@npm run format
	@echo "$(GREEN)Code formatted!$(NC)"

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf dist/ node_modules/.cache coverage/
	@echo "$(GREEN)Clean complete!$(NC)"

check: ## Run all checks (build + lint + test)
	@echo "$(BLUE)Running all checks...$(NC)"
	@npm run check
	@echo "$(GREEN)All checks passed!$(NC)"

# Docker Commands
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t {{SERVICE_NAME}}:latest .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	@docker run -p 8000:8000 {{SERVICE_NAME}}:latest