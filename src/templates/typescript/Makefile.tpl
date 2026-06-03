.PHONY: install dev test typecheck check build run lint fmt format-check{% if has_docker %} docker-build{% endif %}

BUN ?= bun
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install
{% include "_shared/make_logging.mk.tpl" %}
{% if has_docker %}{% include "_shared/make_docker.mk.tpl" %}{% endif %}

install:
	@$(call log,Installing TypeScript dependencies)
	@mkdir -p $(BUN_TMPDIR) $(BUN_CACHE_DIR)/install
	@$(BUN_ENV) $(BUN) install

dev:
	@$(call log,Starting TypeScript dev server)
	@$(BUN_ENV) $(BUN) run dev

test: install
	@$(call log,Running TypeScript tests)
	@$(BUN_ENV) $(BUN) run test

typecheck: install
	@$(call log,Running TypeScript typecheck)
	@$(BUN_ENV) $(BUN) run typecheck

lint: install
	@$(call log,Running ESLint)
	@$(BUN_ENV) $(BUN) run lint

fmt: install
	@$(call log,Formatting TypeScript sources)
	@$(BUN_ENV) $(BUN) run format

format-check: install
	@$(call log,Checking TypeScript formatting)
	@$(BUN_ENV) $(BUN) run format:check

check: lint typecheck test

build: install
	@$(call log,Building TypeScript service)
	@$(BUN_ENV) $(BUN) run build

run: build
	@$(call log,Running TypeScript service)
	@$(BUN_ENV) $(BUN) start

