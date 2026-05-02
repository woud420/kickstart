.PHONY: install check build dev deploy

BUN ?= bun
CARGO ?= cargo

install:
	$(BUN) install

check:
	$(CARGO) check --target wasm32-unknown-unknown

build:
	$(BUN) run build

dev:
	$(BUN) run dev

deploy:
	$(BUN) run deploy
