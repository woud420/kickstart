VENV := .venv
PYTHON := $(VENV)/bin/python
POETRY := poetry

.PHONY: help setup install build run tests clean package shell

help:
	@echo "Usage:"
	@echo "  make setup      - Set up virtualenv + install deps"
	@echo "  make install    - Same as setup"
	@echo "  make build      - Build self-contained kickstart binary"
	@echo "  make run        - Run kickstart CLI from venv"
	@echo "  make tests      - Run pytest tests"
	@echo "  make package    - Package poetry project"
	@echo "  make shell      - Drop into Poetry shell"
	@echo "  make clean      - Remove venv and build artifacts"

setup install:
	@echo "🐍 Creating venv + installing deps..."
	@$(POETRY) install

build:
	@echo "📦 Building kickstart binary with shiv..."
	@$(VENV)/bin/pip install -q shiv || true
	@shiv -c kickstart -o kickstart -e src.cli.main:app --compressed .

run:
	@echo "🚀 Running kickstart..."
	@$(POETRY) run kickstart

tests:
	@echo "🧪 Running tests..."
	@$(POETRY) run pytest

package:
	@$(POETRY) build

shell:
	@$(POETRY) shell

clean:
	rm -rf $(VENV) dist/ kickstart *.egg-info .pytest_cache
