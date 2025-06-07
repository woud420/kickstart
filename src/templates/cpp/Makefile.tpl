.PHONY: dev test build lint clean

BUILD_DIR = build
TEST_DIR = $(BUILD_DIR)/tests

dev:
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && make
	./$(BUILD_DIR)/{{SERVICE_NAME}}

test:
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && make
	cd $(BUILD_DIR) && ctest --output-on-failure

build:
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. && make

lint:
	clang-format -i src/**/*.{hpp,cpp} tests/**/*.cpp

clean:
	rm -rf $(BUILD_DIR) 