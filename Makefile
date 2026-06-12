PYTHON ?= python3
POETRY ?= poetry
POETRY_RUN := $(POETRY) run
PY := PYTHONPATH=$(CURDIR) $(POETRY_RUN) python
PYTEST := $(POETRY_RUN) python -c "import pytest, sys; raise SystemExit(pytest.main(sys.argv[1:]))"

# Directories that Ruff scans for lint + format. Keep mypy narrower (no tests).
LINT_DIRS := src tests ci scripts
MYPY_DIRS := src ci scripts

# Modules PyInstaller can't auto-discover from imports alone.
PYINSTALLER_HIDDEN_IMPORTS := typer rich requests toml jinja2
HIDDEN_IMPORT_ARGS := $(foreach mod,$(PYINSTALLER_HIDDEN_IMPORTS),--hidden-import $(mod))

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
	@echo "  make binary           Build the kickstart binary with PyInstaller"
	@echo "  make build            Build package and binary"
	@echo "  make release-check    Validate release tag policy, requires TAG=vX.Y.Z"
	@echo "  make clean            Remove local build and test artifacts"

setup install:
	@$(call log,Installing project dependencies)
	@$(POETRY) install

run:
	@$(call log,Showing CLI help)
	@$(POETRY_RUN) kickstart --help

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
	@$(POETRY_RUN) mypy $(MYPY_DIRS)

lint:
	@$(call log,Running Ruff lint)
	@$(POETRY_RUN) ruff check $(LINT_DIRS)

format:
	@$(call log,Formatting source, tests, and CI Python)
	@$(POETRY_RUN) ruff format $(LINT_DIRS)

format-check:
	@$(call log,Checking source, tests, and CI Python formatting)
	@$(POETRY_RUN) ruff format --check $(LINT_DIRS)

type-hygiene:
	@$(call log,Auditing type hygiene)
	@$(PY) scripts/type_hygiene_audit.py

template-audit:
	@$(call log,Auditing template wiring)
	@$(PY) scripts/template_wiring_audit.py --strict

check: lint typecheck type-hygiene template-audit tests

package:
	@$(call log,Building Python package)
	@$(POETRY) build

binary:
	@$(call log,Building kickstart binary)
	@$(POETRY_RUN) pyinstaller \
		--name kickstart \
		--onedir \
		--clean \
		--add-data "src/templates:src/templates" \
		$(HIDDEN_IMPORT_ARGS) \
		--collect-all src \
		src/cli/main.py

build: package binary

release-check:
	@test -n "$(TAG)" || (echo "Usage: make release-check TAG=v0.4.1" && exit 1)
	@$(call log,Validating release tag $(TAG))
	@$(PYTHON) ci/release_policy.py --tag "$(TAG)" --version-file pyproject.toml --init-file src/__init__.py

clean:
	@$(call log,Removing local build and test artifacts)
	@rm -rf build/ dist/ kickstart *.egg-info kickstart.spec .pytest_cache .ruff_cache
