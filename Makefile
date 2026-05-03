POETRY ?= poetry
PYTEST := $(POETRY) run python -c "import pytest, sys; raise SystemExit(pytest.main(sys.argv[1:]))"

.PHONY: help setup install run tests test-unit test-integration typecheck lint format format-check type-hygiene template-audit check package binary build clean

help:
	@echo "Usage:"
	@echo "  make setup            Install project dependencies"
	@echo "  make run              Show the kickstart CLI help"
	@echo "  make tests            Run the full test suite"
	@echo "  make test-unit        Run unit tests"
	@echo "  make test-integration Run integration tests"
	@echo "  make typecheck        Run mypy"
	@echo "  make lint             Run Ruff lint checks"
	@echo "  make format           Format source and tests with Ruff"
	@echo "  make format-check     Check Ruff formatting without changing files"
	@echo "  make type-hygiene     Check for loose Any/object-style type annotations"
	@echo "  make template-audit   Check template wiring inventory"
	@echo "  make check            Run lint, typecheck, and tests"
	@echo "  make package          Build wheel and source distribution"
	@echo "  make binary           Build a local standalone binary with PyInstaller"
	@echo "  make build            Build package and standalone binary"
	@echo "  make clean            Remove local build and test artifacts"

setup install:
	@$(POETRY) install

run:
	@$(POETRY) run kickstart --help

tests:
	@PYTHONPATH=$(CURDIR) $(PYTEST)

test-unit:
	@PYTHONPATH=$(CURDIR) $(PYTEST) tests/unit

test-integration:
	@PYTHONPATH=$(CURDIR) $(PYTEST) tests/integration

typecheck:
	@$(POETRY) run mypy src

lint:
	@$(POETRY) run ruff check src tests

format:
	@$(POETRY) run ruff format src tests

format-check:
	@$(POETRY) run ruff format --check src tests

type-hygiene:
	@PYTHONPATH=$(CURDIR) $(POETRY) run python scripts/type_hygiene_audit.py

template-audit:
	@PYTHONPATH=$(CURDIR) $(POETRY) run python scripts/template_wiring_audit.py --strict

check: lint typecheck type-hygiene template-audit tests

package:
	@$(POETRY) build

binary:
	@$(POETRY) run pyinstaller \
		--name kickstart \
		--onefile \
		--clean \
		--add-data "src/templates:src/templates" \
		--hidden-import typer \
		--hidden-import rich \
		--hidden-import requests \
		--hidden-import toml \
		--hidden-import jinja2 \
		--collect-all src \
		src/cli/main.py

build: package binary

clean:
	rm -rf build/ dist/ kickstart *.egg-info kickstart.spec .pytest_cache .ruff_cache
