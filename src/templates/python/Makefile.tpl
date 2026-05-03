.PHONY: install test lint typecheck check build

POETRY ?= poetry
PY_CACHE_DIR ?= $(CURDIR)/.cache
POETRY_ENV = POETRY_IGNORE_ACTIVE_VIRTUALENVS=1 POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_CACHE_DIR=$(PY_CACHE_DIR)/pypoetry PIP_CACHE_DIR=$(PY_CACHE_DIR)/pip $(POETRY)
POETRY_RUN = POETRY_IGNORE_ACTIVE_VIRTUALENVS=1 POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_CACHE_DIR=$(PY_CACHE_DIR)/pypoetry PIP_CACHE_DIR=$(PY_CACHE_DIR)/pip $(POETRY) run

install:
	@mkdir -p $(PY_CACHE_DIR)/pypoetry $(PY_CACHE_DIR)/pip
	$(POETRY_ENV) install
	@if [ -f requirements.txt ]; then $(POETRY_RUN) python -m pip install -r requirements.txt; fi

test: install
	$(POETRY_RUN) python -m pytest

lint: install
	$(POETRY_RUN) ruff check .

typecheck: install
	$(POETRY_RUN) mypy src

check: lint typecheck test

build: install
	$(POETRY_ENV) build
