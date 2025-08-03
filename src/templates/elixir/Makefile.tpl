# {{SERVICE_NAME}} Makefile
.PHONY: help install deps dev test test-watch lint format check clean setup build docker-build docker-run

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Show this help message
	@echo "$(CYAN){{SERVICE_NAME}} - Elixir/Phoenix Service$(RESET)"
	@echo "$(CYAN)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-12s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)First time setup:$(RESET)"
	@echo "  Run '$(GREEN)make setup-asdf$(RESET)' to install asdf and required tools"

install: deps ## Install all dependencies
	@echo "$(CYAN)Installing dependencies...$(RESET)"
	@mix deps.get
	@echo "$(GREEN)✓ Dependencies installed$(RESET)"

deps: ## Get dependencies
	@echo "$(CYAN)Fetching dependencies...$(RESET)"
	@mix deps.get
	@echo "$(GREEN)✓ Dependencies fetched$(RESET)"

setup: install ## Setup the project (install deps + setup database)
	@echo "$(CYAN)Setting up project...$(RESET)"
	@mix ecto.setup
	@echo "$(GREEN)✓ Project setup complete$(RESET)"

dev: ## Start development server
	@echo "$(CYAN)Starting development server...$(RESET)"
	@mix phx.server

test: ## Run all tests
	@echo "$(CYAN)Running tests...$(RESET)"
	@mix test
	@echo "$(GREEN)✓ Tests completed$(RESET)"

test-watch: ## Run tests in watch mode
	@echo "$(CYAN)Running tests in watch mode...$(RESET)"
	@mix test.watch

lint: ## Run code linting
	@echo "$(CYAN)Running linter...$(RESET)"
	@mix credo --strict
	@echo "$(GREEN)✓ Linting completed$(RESET)"

format: ## Format code
	@echo "$(CYAN)Formatting code...$(RESET)"
	@mix format
	@echo "$(GREEN)✓ Code formatted$(RESET)"

format-check: ## Check if code is formatted
	@echo "$(CYAN)Checking code format...$(RESET)"
	@mix format --check-formatted
	@echo "$(GREEN)✓ Code format check completed$(RESET)"

dialyzer: ## Run static analysis
	@echo "$(CYAN)Running Dialyzer...$(RESET)"
	@mix dialyzer
	@echo "$(GREEN)✓ Dialyzer completed$(RESET)"

security: ## Run security analysis
	@echo "$(CYAN)Running security analysis...$(RESET)"
	@mix sobelow --config
	@echo "$(GREEN)✓ Security analysis completed$(RESET)"

check: format-check lint test dialyzer security ## Run all checks (format, lint, test, dialyzer, security)
	@echo "$(GREEN)✓ All checks passed$(RESET)"

clean: ## Clean build artifacts
	@echo "$(CYAN)Cleaning build artifacts...$(RESET)"
	@mix clean
	@rm -rf _build
	@rm -rf deps
	@echo "$(GREEN)✓ Cleaned$(RESET)"

build: ## Build the application
	@echo "$(CYAN)Building application...$(RESET)"
	@mix compile
	@echo "$(GREEN)✓ Build completed$(RESET)"

release: ## Build production release
	@echo "$(CYAN)Building production release...$(RESET)"
	@MIX_ENV=prod mix release
	@echo "$(GREEN)✓ Release built$(RESET)"

# Database commands
db-setup: ## Setup database
	@echo "$(CYAN)Setting up database...$(RESET)"
	@mix ecto.setup
	@echo "$(GREEN)✓ Database setup completed$(RESET)"

db-migrate: ## Run database migrations
	@echo "$(CYAN)Running migrations...$(RESET)"
	@mix ecto.migrate
	@echo "$(GREEN)✓ Migrations completed$(RESET)"

db-rollback: ## Rollback last migration
	@echo "$(CYAN)Rolling back migration...$(RESET)"
	@mix ecto.rollback
	@echo "$(GREEN)✓ Rollback completed$(RESET)"

db-reset: ## Reset database
	@echo "$(CYAN)Resetting database...$(RESET)"
	@mix ecto.reset
	@echo "$(GREEN)✓ Database reset completed$(RESET)"

db-seed: ## Seed database
	@echo "$(CYAN)Seeding database...$(RESET)"
	@mix run priv/repo/seeds.exs
	@echo "$(GREEN)✓ Database seeded$(RESET)"

# Docker commands
docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(RESET)"
	@docker build -t {{SERVICE_NAME}} .
	@echo "$(GREEN)✓ Docker image built$(RESET)"

docker-run: ## Run Docker container
	@echo "$(CYAN)Running Docker container...$(RESET)"
	@docker run -p 4000:4000 --env-file .env {{SERVICE_NAME}}

docker-run-bg: ## Run Docker container in background
	@echo "$(CYAN)Running Docker container in background...$(RESET)"
	@docker run -d -p 4000:4000 --env-file .env --name {{SERVICE_NAME}} {{SERVICE_NAME}}
	@echo "$(GREEN)✓ Container started$(RESET)"

docker-stop: ## Stop Docker container
	@echo "$(CYAN)Stopping Docker container...$(RESET)"
	@docker stop {{SERVICE_NAME}}
	@docker rm {{SERVICE_NAME}}
	@echo "$(GREEN)✓ Container stopped$(RESET)"

# Documentation
docs: ## Generate documentation
	@echo "$(CYAN)Generating documentation...$(RESET)"
	@mix docs
	@echo "$(GREEN)✓ Documentation generated$(RESET)"

# Shell and utilities
shell: ## Start IEx shell with application loaded
	@echo "$(CYAN)Starting IEx shell...$(RESET)"
	@iex -S mix

console: shell ## Alias for shell

# Phoenix specific
routes: ## Show all routes
	@echo "$(CYAN)Application routes:$(RESET)"
	@mix phx.routes

digest: ## Digest and compress static files
	@echo "$(CYAN)Digesting static assets...$(RESET)"
	@mix phx.digest
	@echo "$(GREEN)✓ Assets digested$(RESET)"

# ASDF and version management
setup-asdf: ## Install asdf and required language versions
	@echo "$(CYAN)Setting up asdf version manager...$(RESET)"
	@if ! command -v asdf >/dev/null 2>&1; then \
		echo "$(YELLOW)Installing asdf...$(RESET)"; \
		$(MAKE) install-asdf; \
	else \
		echo "$(GREEN)✓ asdf already installed$(RESET)"; \
	fi
	@echo "$(CYAN)Installing language plugins and versions...$(RESET)"
	@$(MAKE) install-versions
	@echo "$(GREEN)✓ Setup complete! Run 'make install' to get dependencies$(RESET)"

install-asdf: ## Install asdf version manager
	@echo "$(CYAN)Detecting operating system and shell...$(RESET)"
	@CURRENT_SHELL=$$(basename "$$SHELL" 2>/dev/null || echo "bash"); \
	if [ "$$(uname)" = "Darwin" ]; then \
		echo "$(CYAN)Installing asdf on macOS...$(RESET)"; \
		if command -v brew >/dev/null 2>&1; then \
			brew install asdf; \
			ASDF_PATH="$$(brew --prefix asdf)/libexec/asdf"; \
		else \
			echo "$(YELLOW)Homebrew not found. Installing via Git...$(RESET)"; \
			git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0; \
			ASDF_PATH="~/.asdf/asdf"; \
		fi; \
	elif [ "$$(uname)" = "Linux" ]; then \
		echo "$(CYAN)Installing asdf on Linux...$(RESET)"; \
		git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0; \
		ASDF_PATH="~/.asdf/asdf"; \
	else \
		echo "$(RED)Unsupported operating system. Please install asdf manually.$(RESET)"; \
		exit 1; \
	fi; \
	echo "$(YELLOW)Detected shell: $$CURRENT_SHELL$(RESET)"; \
	case "$$CURRENT_SHELL" in \
		zsh) \
			echo "$(CYAN)Adding asdf to ~/.zshrc...$(RESET)"; \
			if [ "$$ASDF_PATH" = "~/.asdf/asdf" ]; then \
				echo '. ~/.asdf/asdf.sh' >> ~/.zshrc; \
			else \
				echo ". $$ASDF_PATH.sh" >> ~/.zshrc; \
			fi; \
			echo "$(GREEN)✓ Added to ~/.zshrc$(RESET)"; \
			;; \
		bash) \
			if [ "$$(uname)" = "Darwin" ]; then \
				BASH_PROFILE=~/.bash_profile; \
			else \
				BASH_PROFILE=~/.bashrc; \
			fi; \
			echo "$(CYAN)Adding asdf to $$BASH_PROFILE...$(RESET)"; \
			if [ "$$ASDF_PATH" = "~/.asdf/asdf" ]; then \
				echo '. ~/.asdf/asdf.sh' >> "$$BASH_PROFILE"; \
			else \
				echo ". $$ASDF_PATH.sh" >> "$$BASH_PROFILE"; \
			fi; \
			echo "$(GREEN)✓ Added to $$BASH_PROFILE$(RESET)"; \
			;; \
		fish) \
			echo "$(CYAN)Adding asdf to ~/.config/fish/config.fish...$(RESET)"; \
			mkdir -p ~/.config/fish; \
			if [ "$$ASDF_PATH" = "~/.asdf/asdf" ]; then \
				echo 'source ~/.asdf/asdf.fish' >> ~/.config/fish/config.fish; \
			else \
				echo "source $$ASDF_PATH.fish" >> ~/.config/fish/config.fish; \
			fi; \
			echo "$(GREEN)✓ Added to ~/.config/fish/config.fish$(RESET)"; \
			;; \
		*) \
			echo "$(YELLOW)Unknown shell '$$CURRENT_SHELL'. Please manually add asdf to your shell profile:$(RESET)"; \
			if [ "$$ASDF_PATH" = "~/.asdf/asdf" ]; then \
				echo "$(CYAN)  . ~/.asdf/asdf.sh$(RESET)"; \
			else \
				echo "$(CYAN)  . $$ASDF_PATH.sh$(RESET)"; \
			fi; \
			;; \
	esac
	@echo "$(YELLOW)Restart your terminal or run 'source' on your shell profile$(RESET)"
	@echo "$(YELLOW)Then run: make install-versions$(RESET)"

install-versions: ## Install Erlang, Elixir, and Node.js via asdf
	@echo "$(CYAN)Installing language plugins...$(RESET)"
	@asdf plugin add erlang https://github.com/asdf-vm/asdf-erlang.git 2>/dev/null || echo "$(YELLOW)Erlang plugin already installed$(RESET)"
	@asdf plugin add elixir https://github.com/asdf-vm/asdf-elixir.git 2>/dev/null || echo "$(YELLOW)Elixir plugin already installed$(RESET)"
	@asdf plugin add nodejs https://github.com/asdf-vm/asdf-nodejs.git 2>/dev/null || echo "$(YELLOW)Node.js plugin already installed$(RESET)"
	@echo "$(CYAN)Installing language versions from .tool-versions...$(RESET)"
	@echo "$(YELLOW)This may take a while (especially Erlang compilation)...$(RESET)"
	@asdf install
	@echo "$(GREEN)✓ All language versions installed$(RESET)"

check-versions: ## Check current language versions
	@echo "$(CYAN)Current language versions:$(RESET)"
	@echo "$(GREEN)Erlang:$(RESET) $$(asdf current erlang 2>/dev/null || echo 'Not installed')"
	@echo "$(GREEN)Elixir:$(RESET) $$(asdf current elixir 2>/dev/null || echo 'Not installed')"
	@echo "$(GREEN)Node.js:$(RESET) $$(asdf current nodejs 2>/dev/null || echo 'Not installed')"

update-versions: ## Update to latest stable versions
	@echo "$(CYAN)Updating to latest stable versions...$(RESET)"
	@asdf install erlang latest
	@asdf install elixir latest
	@asdf install nodejs latest
	@asdf local erlang latest
	@asdf local elixir latest
	@asdf local nodejs latest
	@echo "$(GREEN)✓ Updated to latest versions$(RESET)"

# Default target
.DEFAULT_GOAL := help