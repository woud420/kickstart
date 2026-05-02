.PHONY: install dev test typecheck check prepare-release deploy deploy-release

BUN ?= bun

install:
	$(BUN) install

dev:
	$(BUN) run dev

test:
	$(BUN) run test

typecheck:
	$(BUN) run typecheck

check:
	$(BUN) run check

prepare-release:
	$(BUN) run prepare-release

deploy:
	$(BUN) run deploy

deploy-release:
	$(BUN) run deploy:release
