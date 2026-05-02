.PHONY: install dev test typecheck build run docker-build

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

run:
	$(BUN) start

docker-build:
	docker build -t {{ service_name }}:local .
