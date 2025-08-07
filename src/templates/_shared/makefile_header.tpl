# {{SERVICE_NAME}} Makefile
.PHONY: help {{PHONY_TARGETS}}

# Variables
APP_NAME := {{SERVICE_NAME}}
{{LANGUAGE_VARIABLES}}

# Colors for output
GREEN := \033[0;32m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show available commands
	@echo "$(BLUE){{SERVICE_NAME}} - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
