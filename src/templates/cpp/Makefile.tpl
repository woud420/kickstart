# {{service_name}} Makefile
# C++ Build System with Modern Development Tools

# Variables
APP_NAME := {{service_name}}
BUILD_DIR := build
TEST_DIR := $(BUILD_DIR)/tests
CXX := g++
CMAKE := cmake

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m

.PHONY: help dev test build lint clean install deps format debug release

# Default target
help: ## Show this help message
	@echo "$(BLUE){{service_name}} C++ - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Development Commands
deps: ## Check and install dependencies
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@which $(CXX) > /dev/null || (echo "$(RED)C++ compiler not found$(NC)" && exit 1)
	@which $(CMAKE) > /dev/null || (echo "$(RED)CMake not found$(NC)" && exit 1)
	@echo "$(GREEN)Dependencies satisfied!$(NC)"

build: ## Build the application
	@echo "$(BLUE)Building $(APP_NAME)...$(NC)"
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && $(CMAKE) .. && make
	@echo "$(GREEN)Build complete!$(NC)"

debug: ## Build in debug mode
	@echo "$(BLUE)Building $(APP_NAME) in debug mode...$(NC)"
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && $(CMAKE) -DCMAKE_BUILD_TYPE=Debug .. && make
	@echo "$(GREEN)Debug build complete!$(NC)"

release: ## Build in release mode
	@echo "$(BLUE)Building $(APP_NAME) in release mode...$(NC)"
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && $(CMAKE) -DCMAKE_BUILD_TYPE=Release .. && make
	@echo "$(GREEN)Release build complete!$(NC)"

dev: build ## Build and run the application
	@echo "$(BLUE)Running $(APP_NAME)...$(NC)"
	@./$(BUILD_DIR)/$(APP_NAME)

test: build ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@cd $(BUILD_DIR) && ctest --output-on-failure
	@echo "$(GREEN)Tests completed!$(NC)"

test-verbose: build ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	@cd $(BUILD_DIR) && ctest --verbose

# Code Quality Commands
lint: ## Run clang-format linter
	@echo "$(BLUE)Running clang-format...$(NC)"
	@if command -v clang-format >/dev/null 2>&1; then \
		find src tests -name "*.cpp" -o -name "*.hpp" -o -name "*.h" | xargs clang-format --dry-run --Werror; \
		echo "$(GREEN)Linting complete!$(NC)"; \
	else \
		echo "$(YELLOW)clang-format not found, skipping lint$(NC)"; \
	fi

format: ## Format code with clang-format
	@echo "$(BLUE)Formatting code...$(NC)"
	@if command -v clang-format >/dev/null 2>&1; then \
		find src tests -name "*.cpp" -o -name "*.hpp" -o -name "*.h" | xargs clang-format -i; \
		echo "$(GREEN)Code formatting complete!$(NC)"; \
	else \
		echo "$(YELLOW)clang-format not found, skipping format$(NC)"; \
	fi

analyze: ## Run static analysis (if available)
	@echo "$(BLUE)Running static analysis...$(NC)"
	@if command -v cppcheck >/dev/null 2>&1; then \
		cppcheck --enable=all --std=c++17 src/; \
		echo "$(GREEN)Static analysis complete!$(NC)"; \
	else \
		echo "$(YELLOW)cppcheck not found, skipping analysis$(NC)"; \
	fi

# Docker Commands
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t {{service_name}}:latest .
	@echo "$(GREEN)Docker image built!$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	@docker run -p 8080:8080 {{service_name}}:latest

# Debugging Commands
debug-gdb: debug ## Run with GDB debugger
	@echo "$(BLUE)Starting GDB session...$(NC)"
	@gdb ./$(BUILD_DIR)/$(APP_NAME)

debug-valgrind: debug ## Run with Valgrind
	@echo "$(BLUE)Running with Valgrind...$(NC)"
	@if command -v valgrind >/dev/null 2>&1; then \
		valgrind --leak-check=full --show-leak-kinds=all ./$(BUILD_DIR)/$(APP_NAME); \
	else \
		echo "$(YELLOW)Valgrind not found$(NC)"; \
	fi

# Utility Commands
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf $(BUILD_DIR)
	@echo "$(GREEN)Clean complete!$(NC)"

install: release ## Install the application
	@echo "$(BLUE)Installing $(APP_NAME)...$(NC)"
	@cd $(BUILD_DIR) && make install
	@echo "$(GREEN)Installation complete!$(NC)"

info: ## Show build information
	@echo "$(BLUE)Build Information:$(NC)"
	@echo "  App Name: $(APP_NAME)"
	@echo "  Build Dir: $(BUILD_DIR)"
	@echo "  Compiler: $(CXX)"
	@echo "  CMake: $(CMAKE)"

# Combined Commands
check: format lint test ## Run all checks (format, lint, test)
	@echo "$(GREEN)All checks passed!$(NC)"

all: clean deps build test ## Clean, build, and test
	@echo "$(GREEN)Build pipeline completed!$(NC)" 
