.PHONY: install dev test typecheck check deploy

BUN ?= bun
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install

install:
	@mkdir -p $(BUN_TMPDIR) $(BUN_CACHE_DIR)/install
	$(BUN_ENV) $(BUN) install

dev:
	$(BUN_ENV) $(BUN) run dev

test: install
	$(BUN_ENV) $(BUN) run test

typecheck: install
	$(BUN_ENV) $(BUN) run typecheck

check: typecheck test

deploy:
	$(BUN_ENV) $(BUN) run deploy
