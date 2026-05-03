.PHONY: install test typecheck check ensure-worker-build ensure-wasm-target worker-build-release build dev deploy

BUN ?= bun
CARGO ?= cargo
RUSTC ?= rustc
WORKER_BUILD ?= worker-build
WASM_TARGET ?= wasm32-unknown-unknown
BUN_TMPDIR ?= $(CURDIR)/.tmp
BUN_CACHE_DIR ?= $(CURDIR)/.cache/bun
BUN_ENV = TMPDIR=$(BUN_TMPDIR) XDG_CACHE_HOME=$(CURDIR)/.cache BUN_INSTALL_CACHE_DIR=$(BUN_CACHE_DIR)/install

install:
	@mkdir -p $(BUN_TMPDIR) $(BUN_CACHE_DIR)/install
	$(BUN_ENV) $(BUN) install

test: install
	$(CARGO) test

typecheck: install
	$(CARGO) check

check: typecheck test

ensure-worker-build:
	@command -v $(WORKER_BUILD) >/dev/null 2>&1 || $(CARGO) install worker-build --locked

ensure-wasm-target:
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
	$(WORKER_BUILD) --release

build: install worker-build-release

dev:
	$(BUN_ENV) $(BUN) run dev

deploy:
	$(BUN_ENV) $(BUN) run deploy
