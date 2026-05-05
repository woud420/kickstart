.PHONY: install dev test typecheck check build run docker-build

BUN ?= bun
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install
{% include "_shared/make_logging.mk.tpl" %}

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

check: typecheck test

build: install
	@$(call log,Building TypeScript service)
	@$(BUN_ENV) $(BUN) run build

run: build
	@$(call log,Running TypeScript service)
	@$(BUN_ENV) $(BUN) start

docker-build:
	@$(call log,Building Docker image)
	@docker build -t {{ service_name }}:local .
