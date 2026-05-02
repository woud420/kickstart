.PHONY: install dev test typecheck build preview

BUN ?= bun

install:
	$(BUN) install

dev:
	$(BUN) run dev

test:
	$(BUN) run test

typecheck:
	$(BUN) run typecheck

build:
	$(BUN) run build

preview:
	$(BUN) run preview
