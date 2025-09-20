cmake_minimum_required(VERSION 3.14)
project({{service_name}} VERSION 0.2.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add source files
file(GLOB_RECURSE SOURCES "src/*.cpp")

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Add include directories
target_include_directories(${PROJECT_NAME} PRIVATE src)

# Add test executable
enable_testing()
add_executable(${PROJECT_NAME}_tests
    tests/api/routes_test.cpp
    tests/api/models_test.cpp
    tests/core/config_test.cpp
    tests/services/service_test.cpp
)

target_include_directories(${PROJECT_NAME}_tests PRIVATE src)
add_test(NAME ${PROJECT_NAME}_tests COMMAND ${PROJECT_NAME}_tests) 