VENV := .venv
PYTHON := $(VENV)/bin/python
POETRY := $(VENV)/bin/poetry
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

.PHONY: help setup install build run tests test-unit test-integration typecheck lint format clean package shell venv

help:
	@echo "Usage:"
	@echo "  make setup      - Set up virtualenv + install deps"
	@echo "  make install    - Same as setup"
	@echo "  make build      - Build self-contained kickstart binary"
	@echo "  make run        - Run kickstart CLI from venv"
	@echo "  make tests      - Run all tests"
	@echo "  make test-unit  - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make typecheck  - Run mypy type checking"
	@echo "  make lint       - Run linting (placeholder)"
	@echo "  make format     - Run code formatting (placeholder)"
	@echo "  make package    - Package poetry project"
	@echo "  make shell      - Drop into Poetry shell"
	@echo "  make clean      - Remove venv and build artifacts"

venv: $(VENV)/bin/activate

$(VENV)/bin/activate:
	@echo "🐍 Creating virtual environment..."
	@which python3 > /dev/null || (echo "Error: python3 not found. Please install Python 3." && exit 1)
	@python3 -m venv $(VENV)
	@$(PIP) install poetry

setup install: venv
	@echo "📦 Installing dependencies..."
	@$(POETRY) install
	@$(PIP) install pytest

build: venv
	@echo "📦 Building kickstart binary..."
	@$(POETRY) install
	@ln -sf $$($(POETRY) env info --path)/bin/kickstart kickstart

run: venv
	@echo "🚀 Running kickstart..."
	@$(POETRY) run kickstart

tests: test-unit test-integration typecheck
	@echo "✅ All tests completed!"

test-unit: venv setup
	@echo "🧪 Running unit tests..."
	@PATH="$$(pwd):$$PATH" $(PYTEST) tests/unit/

test-integration: venv setup build
	@echo "🧪 Running integration tests..."
	@PATH="$$(pwd):$$PATH" $(PYTEST) tests/integration/

typecheck: venv setup
	@echo "🔍 Running mypy type checking..."
	@$(VENV)/bin/mypy src/

lint: venv setup
	@echo "🔧 Running linting..."
	@echo "  (Linting not yet configured - add ruff or flake8 here)"

format: venv setup
	@echo "🎨 Running code formatting..."
	@echo "  (Formatting not yet configured - add black or ruff here)"

package: venv
	@$(POETRY) build

shell: venv
	@$(POETRY) shell

clean:
	rm -rf $(VENV) dist/ kickstart *.egg-info .pytest_cache
