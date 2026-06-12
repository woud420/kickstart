.PHONY: install dev test typecheck check build lint fmt format-check clean{% if has_docker %} docker-build{% endif %}

BUILD_DIR = build
{% include "_shared/make_logging.mk.tpl" %}
{% if has_docker %}{% include "_shared/make_docker.mk.tpl" %}{% endif %}

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

fmt:
	@$(call log,Formatting C++ sources)
	@command -v clang-format
	@find src tests -type f \( -name '*.hpp' -o -name '*.cpp' \) 2>/dev/null | xargs -r clang-format -i

format-check:
	@$(call log,Checking C++ formatting)
	@command -v clang-format
	@find src tests -type f \( -name '*.hpp' -o -name '*.cpp' \) 2>/dev/null | xargs -r clang-format --dry-run --Werror

lint: format-check

clean:
	@$(call log,Removing C++ build artifacts)
	@rm -rf $(BUILD_DIR)
