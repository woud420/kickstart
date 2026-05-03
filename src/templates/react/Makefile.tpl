.PHONY: install dev test typecheck check build preview

BUN ?= bun
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install
{% include "_shared/make_logging.mk.tpl" %}

install:
	@$(call log,Installing frontend dependencies)
	@mkdir -p $(BUN_TMPDIR) $(BUN_CACHE_DIR)/install
	@$(BUN_ENV) $(BUN) install

dev:
	@$(call log,Starting frontend dev server)
	@$(BUN_ENV) $(BUN) run dev

test: install
	@$(call log,Running frontend tests)
	@$(BUN_ENV) $(BUN) run test

typecheck: install
	@$(call log,Running frontend typecheck)
	@$(BUN_ENV) $(BUN) run typecheck

check: typecheck test

build: install
	@$(call log,Building frontend)
	@$(BUN_ENV) $(BUN) run build

preview:
	@$(call log,Starting frontend preview)
	@$(BUN_ENV) $(BUN) run preview
