.PHONY: install test typecheck check build dev deploy

BUN ?= bun
CARGO ?= cargo
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install

install:
	@mkdir -p $(BUN_TMPDIR) $(BUN_CACHE_DIR)/install
	$(BUN_ENV) $(BUN) install

test: install
	$(CARGO) test

typecheck: install
	$(CARGO) check

check: typecheck test

build: install
	$(BUN_ENV) $(BUN) run build

dev:
	$(BUN_ENV) $(BUN) run dev

deploy:
	$(BUN_ENV) $(BUN) run deploy
