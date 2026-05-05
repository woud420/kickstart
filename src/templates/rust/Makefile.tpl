.PHONY: install dev test typecheck check build lint
{% include "_shared/make_logging.mk.tpl" %}

install:
	@$(call log,Fetching Rust dependencies)
	@cargo fetch

dev: install
	@$(call log,Running Rust service)
	@cargo run

test: install
	@$(call log,Running Rust tests)
	@cargo test

typecheck: install
	@$(call log,Running Rust typecheck)
	@cargo check

check: lint typecheck test

build: install
	@$(call log,Building Rust release)
	@cargo build --release

lint:
	@$(call log,Checking Rust formatting)
	@cargo fmt --all -- --check
