PYTHON ?= python3
POETRY ?= poetry
PYTEST := $(POETRY) run python -c "import pytest, sys; raise SystemExit(pytest.main(sys.argv[1:]))"

LOG_COLOR ?= \033[1;34m
LOG_RESET ?= \033[0m
ifdef NO_COLOR
LOG_COLOR :=
LOG_RESET :=
endif
log = printf "$(LOG_COLOR)==>$(LOG_RESET) %s\n" "$(1)"

.PHONY: help setup install run tests test-unit test-integration typecheck lint format format-check type-hygiene template-audit check package binary build release-check clean

help:
	@echo "Usage:"
	@echo "  make setup            Install project dependencies"
	@echo "  make run              Show the kickstart CLI help"
	@echo "  make tests            Run the full test suite"
	@echo "  make test-unit        Run unit tests"
	@echo "  make test-integration Run integration tests"
	@echo "  make typecheck        Run mypy"
	@echo "  make lint             Run Ruff lint checks"
	@echo "  make format           Format source, tests, and CI Python with Ruff"
	@echo "  make format-check     Check Ruff formatting without changing files"
	@echo "  make type-hygiene     Check for loose Any/object-style type annotations"
	@echo "  make template-audit   Check template wiring inventory"
	@echo "  make check            Run lint, typecheck, and tests"
	@echo "  make package          Build wheel and source distribution"
	@echo "  make binary           Build a local standalone binary with PyInstaller"
	@echo "  make build            Build package and standalone binary"
	@echo "  make release-check    Validate release tag policy, requires TAG=vX.Y.Z"
	@echo "  make clean            Remove local build and test artifacts"

setup install:
	@$(call log,Installing project dependencies)
	@$(POETRY) install

run:
	@$(call log,Showing CLI help)
	@$(POETRY) run kickstart --help

tests:
	@$(call log,Running full test suite)
	@PYTHONPATH=$(CURDIR) $(PYTEST)

test-unit:
	@$(call log,Running unit tests)
	@PYTHONPATH=$(CURDIR) $(PYTEST) tests/unit

test-integration:
	@$(call log,Running integration tests)
	@PYTHONPATH=$(CURDIR) $(PYTEST) tests/integration

typecheck:
	@$(call log,Running mypy)
	@$(POETRY) run mypy src ci

lint:
	@$(call log,Running Ruff lint)
	@$(POETRY) run ruff check src tests ci

format:
	@$(call log,Formatting source, tests, and CI Python)
	@$(POETRY) run ruff format src tests ci

format-check:
	@$(call log,Checking source, tests, and CI Python formatting)
	@$(POETRY) run ruff format --check src tests ci

type-hygiene:
	@$(call log,Auditing type hygiene)
	@PYTHONPATH=$(CURDIR) $(POETRY) run python scripts/type_hygiene_audit.py

template-audit:
	@$(call log,Auditing template wiring)
	@PYTHONPATH=$(CURDIR) $(POETRY) run python scripts/template_wiring_audit.py --strict

check: lint typecheck type-hygiene template-audit tests

package:
	@$(call log,Building Python package)
	@$(POETRY) build

binary:
	@$(call log,Building standalone binary)
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

release-check:
	@test -n "$(TAG)" || (echo "Usage: make release-check TAG=v0.4.1" && exit 1)
	@$(call log,Validating release tag $(TAG))
	@$(PYTHON) ci/release_policy.py --tag "$(TAG)" --version-file pyproject.toml

clean:
	@$(call log,Removing local build and test artifacts)
	@rm -rf build/ dist/ kickstart *.egg-info kickstart.spec .pytest_cache .ruff_cache
