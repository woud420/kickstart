.PHONY: install dev test typecheck check build lint fmt clean{% if has_docker %} docker-build{% endif %}
{% include "_shared/make_logging.mk.tpl" %}
{% if has_docker %}{% include "_shared/make_docker.mk.tpl" %}{% endif %}

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

fmt:
	@$(call log,Formatting Rust sources)
	@cargo fmt --all

lint:
	@$(call log,Checking Rust formatting)
	@cargo fmt --all -- --check
	@$(call log,Running Clippy)
	@cargo clippy --all-targets --all-features -- -D warnings

clean:
	@$(call log,Cleaning Rust build artifacts)
	@cargo clean
