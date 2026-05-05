.PHONY: install test lint typecheck check build

POETRY ?= poetry
PY_CACHE_DIR ?= $(CURDIR)/.cache
POETRY_ENV = POETRY_IGNORE_ACTIVE_VIRTUALENVS=1 POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_CACHE_DIR=$(PY_CACHE_DIR)/pypoetry PIP_CACHE_DIR=$(PY_CACHE_DIR)/pip $(POETRY)
POETRY_RUN = POETRY_IGNORE_ACTIVE_VIRTUALENVS=1 POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_CACHE_DIR=$(PY_CACHE_DIR)/pypoetry PIP_CACHE_DIR=$(PY_CACHE_DIR)/pip $(POETRY) run
{% include "_shared/make_logging.mk.tpl" %}

install:
	@$(call log,Installing Python dependencies)
	@mkdir -p $(PY_CACHE_DIR)/pypoetry $(PY_CACHE_DIR)/pip
	@$(POETRY_ENV) install
	@if [ -f requirements.txt ]; then $(POETRY_RUN) python -m pip install -r requirements.txt; fi

test: install
	@$(call log,Running Python tests)
	@$(POETRY_RUN) python -m pytest

lint: install
	@$(call log,Running Ruff lint)
	@$(POETRY_RUN) ruff check .

typecheck: install
	@$(call log,Running mypy)
	@$(POETRY_RUN) mypy src

check: lint typecheck test

build: install
	@$(call log,Building Python package)
	@$(POETRY_ENV) build
