.PHONY: dev test build lint clean

BUILD_DIR = build

dev:
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && cmake --build .
	./$(BUILD_DIR)/{{ service_name }}

test:
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && cmake --build .
	cd $(BUILD_DIR) && ctest --output-on-failure

build:
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && cmake --build .

lint:
	clang-format -i src/**/*.hpp src/**/*.cpp tests/**/*.cpp

clean:
	rm -rf $(BUILD_DIR)
