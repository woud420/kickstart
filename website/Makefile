.PHONY: install dev test typecheck check prepare-release deploy deploy-release

BUN ?= bun
LOG_COLOR ?= \033[1;34m
LOG_RESET ?= \033[0m
ifdef NO_COLOR
LOG_COLOR :=
LOG_RESET :=
endif
log = printf "$(LOG_COLOR)==>$(LOG_RESET) %s\n" "$(1)"

install:
	@$(call log,Installing website dependencies)
	@$(BUN) install

dev:
	@$(call log,Starting website dev server)
	@$(BUN) run dev

test:
	@$(call log,Running website tests)
	@$(BUN) run test

typecheck:
	@$(call log,Running website typecheck)
	@$(BUN) run typecheck

check:
	@$(call log,Running website checks)
	@$(BUN) run check

prepare-release:
	@$(call log,Preparing release Wrangler config)
	@$(BUN) run prepare-release

deploy:
	@$(call log,Deploying website with Alchemy)
	@$(BUN) run deploy

deploy-release:
	@$(call log,Deploying release website with Alchemy)
	@$(BUN) run deploy:release
