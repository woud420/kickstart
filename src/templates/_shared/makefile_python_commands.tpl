install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies with uv...$(NC)"
	@uv sync --dev
	@echo "$(GREEN)Dependencies installed!$(NC)"

dev: ## Start development server
	@echo "$(BLUE)Starting development server...$(NC)"
	@uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

build: ## Build the application
	@echo "$(BLUE)Building application...$(NC)"
	@uv build
	@echo "$(GREEN)Build complete!$(NC)"

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@uv run pytest -v

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@uv run pytest --tb=short -q --disable-warnings -x -vvv --ff -l

lint: ## Run linting
	@echo "$(BLUE)Running linters...$(NC)"
	@uv run ruff check .
	@uv run mypy src/

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@uv run black .
	@uv run ruff check --fix .
	@echo "$(GREEN)Code formatted!$(NC)"

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf dist/ build/ *.egg-info .pytest_cache __pycache__ .mypy_cache .ruff_cache
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete!$(NC)"

check: lint test ## Run all checks (lint + test)
