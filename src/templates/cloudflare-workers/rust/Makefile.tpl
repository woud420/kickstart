.PHONY: install test typecheck check ensure-worker-build ensure-wasm-target worker-build-release build dev deploy

BUN ?= bun
CARGO ?= cargo
RUSTC ?= rustc
WORKER_BUILD ?= worker-build
WASM_TARGET ?= wasm32-unknown-unknown
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install
{% include "_shared/make_logging.mk.tpl" %}

install:
	@$(call log,Installing Worker dependencies)
	@mkdir -p $(BUN_TMPDIR) $(BUN_CACHE_DIR)/install
	@$(BUN_ENV) $(BUN) install

test: install
	@$(call log,Running Rust tests)
	@$(CARGO) test

typecheck: install
	@$(call log,Running Rust typecheck)
	@$(CARGO) check

check: typecheck test

ensure-worker-build:
	@$(call log,Checking worker-build)
	@command -v $(WORKER_BUILD) >/dev/null 2>&1 || $(CARGO) install worker-build --locked

ensure-wasm-target:
	@$(call log,Checking Rust WASM target)
	@target_libdir="$$( $(RUSTC) --print target-libdir --target $(WASM_TARGET) 2>/dev/null )"; \
	if [ -z "$$target_libdir" ] || [ ! -d "$$target_libdir" ]; then \
		if command -v rustup >/dev/null 2>&1; then \
			rustup target add $(WASM_TARGET); \
		else \
			echo "Missing Rust target $(WASM_TARGET). Install rustup and run 'rustup target add $(WASM_TARGET)', or use a Rust toolchain that includes it."; \
			exit 1; \
		fi; \
	fi

worker-build-release: ensure-worker-build ensure-wasm-target
	@$(call log,Building Worker release)
	@$(WORKER_BUILD) --release

build: install worker-build-release

dev:
	@$(call log,Starting Worker dev server)
	@$(BUN_ENV) $(BUN) run dev

deploy:
	@$(call log,Deploying Worker)
	@$(BUN_ENV) $(BUN) run deploy
