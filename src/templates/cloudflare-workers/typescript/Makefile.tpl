.PHONY: install dev test typecheck deploy

BUN ?= bun

install:
	$(BUN) install

dev:
	$(BUN) run dev

test:
	$(BUN) run test

typecheck:
	$(BUN) run typecheck

deploy:
	$(BUN) run deploy
