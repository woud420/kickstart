# {{service_name}} Makefile

# Variables
APP_NAME := {{service_name}}
PACKAGE_MANAGER := $(shell which bun > /dev/null 2>&1 && echo "bun" || echo "npm")

# Colors for output
GREEN := \033[0;32m
BLUE := \033[0;34m
NC := \033[0m

.PHONY: help install dev build test clean docker-build docker-run

# Default target
help: ## Show this help message
	@echo "$(BLUE){{service_name}} - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Development Commands
install: ## Install dependencies
	@$(PACKAGE_MANAGER) install

dev: ## Start development server
	@$(PACKAGE_MANAGER) run dev

build: ## Build for production
	@$(PACKAGE_MANAGER) run build

test: ## Run all tests
	@$(PACKAGE_MANAGER) run test

clean: ## Clean build artifacts and node_modules
	@rm -rf dist node_modules .turbo

# Docker Commands
docker-build: ## Build Docker image
	@docker build -t $(APP_NAME):latest .

docker-run: ## Run Docker container
	@docker run -p 3000:3000 $(APP_NAME):latest
