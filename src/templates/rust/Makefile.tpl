.PHONY: install dev test typecheck check build lint

install:
	cargo fetch

dev: install
	cargo run

test: install
	cargo test

typecheck: install
	cargo check

check: lint typecheck test

build: install
	cargo build --release

lint:
	cargo fmt --all -- --check
