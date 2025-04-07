.PHONY: dev test build lint

dev:
	cargo run

test:
	cargo test

build:
	cargo build --release

lint:
	cargo fmt --all
