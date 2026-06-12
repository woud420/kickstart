.PHONY: install dev test lint fmt format-check typecheck check build clean

POETRY ?= poetry
PY_CACHE_DIR ?= $(CURDIR)/.cache
POETRY_ENV = env -u VIRTUAL_ENV POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_CACHE_DIR=$(PY_CACHE_DIR)/pypoetry PIP_CACHE_DIR=$(PY_CACHE_DIR)/pip $(POETRY)
POETRY_RUN = env -u VIRTUAL_ENV POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_CACHE_DIR=$(PY_CACHE_DIR)/pypoetry PIP_CACHE_DIR=$(PY_CACHE_DIR)/pip $(POETRY) run
{% include "_shared/make_logging.mk.tpl" %}

install:
	@$(call log,Installing Python CLI dependencies)
	@mkdir -p $(PY_CACHE_DIR)/pypoetry $(PY_CACHE_DIR)/pip
	@$(POETRY_ENV) install

dev: install
	@$(call log,Running Python CLI)
	@$(POETRY_RUN) python -m src.main check

test: install
	@$(call log,Running Python tests)
	@$(POETRY_RUN) python -m pytest

lint: install
	@$(call log,Running Ruff lint)
	@$(POETRY_RUN) ruff check .

fmt: install
	@$(call log,Formatting Python sources)
	@$(POETRY_RUN) ruff format .
	@$(POETRY_RUN) ruff check --fix .

format-check: install
	@$(call log,Checking Python formatting)
	@$(POETRY_RUN) ruff format --check .

typecheck: install
	@$(call log,Running mypy)
	@$(POETRY_RUN) mypy src

check: lint typecheck test

build: install
	@$(call log,Building Python CLI package)
	@$(POETRY_ENV) build

clean:
	@$(call log,Cleaning Python build artifacts)
	@rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	@find . -type d -name __pycache__ -exec rm -rf {} +
