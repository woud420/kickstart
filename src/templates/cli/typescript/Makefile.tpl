.PHONY: install dev test typecheck check build run

BUN ?= bun
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install
{% include "_shared/make_logging.mk.tpl" %}

install:
	@$(call log,Installing TypeScript CLI dependencies)
	@mkdir -p $(BUN_TMPDIR) $(BUN_CACHE_DIR)/install
	@$(BUN_ENV) $(BUN) install

dev: install
	@$(call log,Running TypeScript CLI)
	@$(BUN_ENV) $(BUN) run dev

test: install
	@$(call log,Running TypeScript tests)
	@$(BUN_ENV) $(BUN) run test

typecheck: install
	@$(call log,Running TypeScript typecheck)
	@$(BUN_ENV) $(BUN) run typecheck

check: typecheck test

build: install
	@$(call log,Building TypeScript CLI)
	@$(BUN_ENV) $(BUN) run build

run: build
	@$(call log,Running built TypeScript CLI)
	@$(BUN_ENV) $(BUN) start
