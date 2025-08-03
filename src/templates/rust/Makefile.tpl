# {{SERVICE_NAME}} Makefile
.PHONY: help install dev build test lint format clean check

# Variables
APP_NAME := {{SERVICE_NAME}}
CARGO := cargo

# Colors for output
GREEN := \033[0;32m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show available commands
	@echo "$(BLUE){{SERVICE_NAME}} - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies and tools
	@echo "$(BLUE)Installing Rust tools...$(NC)"
	@rustup component add clippy rustfmt
	@echo "$(GREEN)Tools installed!$(NC)"

dev: ## Start development server with auto-reload
	@echo "$(BLUE)Starting development server...$(NC)"
	@cargo install cargo-watch
	@cargo watch -x 'run'

build: ## Build the application
	@echo "$(BLUE)Building application...$(NC)"
	@$(CARGO) build --release
	@echo "$(GREEN)Build complete!$(NC)"

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(CARGO) test

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@cargo install cargo-watch
	@cargo watch -x test

lint: ## Run linting
	@echo "$(BLUE)Running linters...$(NC)"
	@$(CARGO) clippy -- -D warnings

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(CARGO) fmt
	@echo "$(GREEN)Code formatted!$(NC)"

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@$(CARGO) clean
	@echo "$(GREEN)Clean complete!$(NC)"

check: lint test ## Run all checks (lint + test)

# Docker Commands
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t $(APP_NAME):latest .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	@docker run -p 8000:8000 $(APP_NAME):latest
