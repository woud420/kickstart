.PHONY: install dev test lint fmt format-check typecheck check build clean{% if has_docker %} docker-build{% endif %}

POETRY ?= poetry
PY_CACHE_DIR ?= $(CURDIR)/.cache
POETRY_ENV = POETRY_IGNORE_ACTIVE_VIRTUALENVS=1 POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_CACHE_DIR=$(PY_CACHE_DIR)/pypoetry PIP_CACHE_DIR=$(PY_CACHE_DIR)/pip $(POETRY)
POETRY_RUN = POETRY_IGNORE_ACTIVE_VIRTUALENVS=1 POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_CACHE_DIR=$(PY_CACHE_DIR)/pypoetry PIP_CACHE_DIR=$(PY_CACHE_DIR)/pip $(POETRY) run
{% include "_shared/make_logging.mk.tpl" %}
{% if has_docker %}{% include "_shared/make_docker.mk.tpl" %}{% endif %}

install:
	@$(call log,Installing Python dependencies)
	@mkdir -p $(PY_CACHE_DIR)/pypoetry $(PY_CACHE_DIR)/pip
	@$(POETRY_ENV) install
	@if [ -f requirements.txt ]; then $(POETRY_RUN) python -m pip install -r requirements.txt; fi

dev: install
	@$(call log,Running Python service)
	@$(POETRY_RUN) python -m src.main

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
	@$(call log,Building Python package)
	@$(POETRY_ENV) build

clean:
	@$(call log,Cleaning Python build artifacts)
	@rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	@find . -type d -name __pycache__ -exec rm -rf {} +
