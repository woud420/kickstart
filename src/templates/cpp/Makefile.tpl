.PHONY: install dev test typecheck check build lint clean

BUILD_DIR = build
{% include "_shared/make_logging.mk.tpl" %}

install:
	@$(call log,Checking C++ toolchain)
	@command -v cmake
	@command -v c++

dev: install
	@$(call log,Building and running C++ service)
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && cmake .. && cmake --build .
	@./$(BUILD_DIR)/{{ service_name }}

test: install
	@$(call log,Running C++ tests)
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && cmake .. && cmake --build .
	@cd $(BUILD_DIR) && ctest --output-on-failure

typecheck: build

check: lint typecheck test

build: install
	@$(call log,Building C++ service)
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && cmake .. && cmake --build .

lint:
	@$(call log,Checking C++ formatting)
	@command -v clang-format
	@clang-format --dry-run --Werror src/**/*.hpp src/**/*.cpp tests/**/*.cpp

clean:
	@$(call log,Removing C++ build artifacts)
	@rm -rf $(BUILD_DIR)
