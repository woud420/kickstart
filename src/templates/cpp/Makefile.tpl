.PHONY: install dev test typecheck check build lint clean

BUILD_DIR = build

install:
	command -v cmake
	command -v c++

dev: install
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && cmake --build .
	./$(BUILD_DIR)/{{ service_name }}

test: install
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && cmake --build .
	cd $(BUILD_DIR) && ctest --output-on-failure

typecheck: build

check: test

build: install
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && cmake --build .

lint:
	command -v clang-format
	clang-format --dry-run --Werror src/**/*.hpp src/**/*.cpp tests/**/*.cpp

clean:
	rm -rf $(BUILD_DIR)
