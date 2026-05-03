.PHONY: install dev test typecheck check deploy

BUN ?= bun
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install
LOG_COLOR ?= \033[1;34m
LOG_RESET ?= \033[0m
ifdef NO_COLOR
LOG_COLOR :=
LOG_RESET :=
endif
log = printf "$(LOG_COLOR)==>$(LOG_RESET) %s\n" "$(1)"

install:
	@$(call log,Installing Worker dependencies)
	@mkdir -p $(BUN_TMPDIR) $(BUN_CACHE_DIR)/install
	@$(BUN_ENV) $(BUN) install

dev:
	@$(call log,Starting Worker dev server)
	@$(BUN_ENV) $(BUN) run dev

test: install
	@$(call log,Running Worker tests)
	@$(BUN_ENV) $(BUN) run test

typecheck: install
	@$(call log,Running Worker typecheck)
	@$(BUN_ENV) $(BUN) run typecheck

check: typecheck test

deploy:
	@$(call log,Deploying Worker)
	@$(BUN_ENV) $(BUN) run deploy
