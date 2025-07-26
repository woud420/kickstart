"""Language-specific configuration for template composition."""

LANGUAGE_CONFIG = {
    "python": {
        "DEFAULT_PORT": "8000",
        "DESCRIPTION": "A Python service built with FastAPI.",
        "PREREQUISITES": "- Python 3.11+\n- [uv](https://docs.astral.sh/uv/) for dependency management",
        "LANGUAGE_VARIABLES": "",
        "LANGUAGE_ENV_VARS": "DEBUG=true\nLOG_LEVEL=INFO",
        "PHONY_TARGETS": "install dev build test lint format clean",
        "COMMAND_LIST": "make install       # Install dependencies with uv\nmake dev           # Start development server with hot reload\nmake build         # Build the application\nmake test          # Run all tests\nmake test-watch    # Run tests in watch mode\nmake lint          # Run linting (ruff + mypy)\nmake format        # Format code (black + ruff)\nmake clean         # Clean build artifacts\nmake check         # Run all checks (lint + test)"
    },
    "rust": {
        "DEFAULT_PORT": "8000",
        "DESCRIPTION": "A Rust service built with Actix-web.",
        "PREREQUISITES": "- Rust 1.70+ (install via [rustup](https://rustup.rs/))\n- `cargo` package manager",
        "LANGUAGE_VARIABLES": "CARGO := cargo",
        "LANGUAGE_ENV_VARS": "RUST_LOG=info",
        "PHONY_TARGETS": "install dev build test lint format clean check",
        "COMMAND_LIST": "make install       # Install Rust tools (clippy, rustfmt)\nmake dev           # Start development server with auto-reload\nmake build         # Build release binary\nmake test          # Run all tests\nmake test-watch    # Run tests in watch mode\nmake lint          # Run clippy linting\nmake format        # Format code with rustfmt\nmake clean         # Clean build artifacts\nmake check         # Run all checks (lint + test)"
    },
    "go": {
        "DEFAULT_PORT": "8000",
        "DESCRIPTION": "A Go service built with Gin framework.",
        "PREREQUISITES": "- Go 1.22+ (install via [go.dev](https://golang.org/dl/))\n- `go mod` for dependency management",
        "LANGUAGE_VARIABLES": "GO := go",
        "LANGUAGE_ENV_VARS": "GIN_MODE=debug",
        "PHONY_TARGETS": "install dev build test lint format clean check",
        "COMMAND_LIST": "make install       # Install Go dependencies and tools\nmake dev           # Start development server with auto-reload\nmake build         # Build release binary\nmake test          # Run all tests\nmake test-watch    # Run tests in watch mode\nmake lint          # Run linting (go vet + staticcheck)\nmake format        # Format code (go fmt + goimports)\nmake clean         # Clean build artifacts\nmake check         # Run all checks (lint + test)"
    },
    "typescript": {
        "DEFAULT_PORT": "8000",
        "DESCRIPTION": "A TypeScript service built with Express.js.",
        "PREREQUISITES": "- Node.js 18+ (install via [nodejs.org](https://nodejs.org/))\n- npm or yarn package manager",
        "LANGUAGE_VARIABLES": "",
        "LANGUAGE_ENV_VARS": "NODE_ENV=development",
        "PHONY_TARGETS": "install dev build test lint format clean check",
        "COMMAND_LIST": "make install       # Install dependencies via npm\nmake dev           # Start development server with auto-reload\nmake build         # Build TypeScript to JavaScript\nmake start         # Start production server\nmake test          # Run tests with Jest\nmake test-watch    # Run tests in watch mode\nmake lint          # Run ESLint\nmake format        # Format code with Prettier\nmake clean         # Clean build artifacts\nmake check         # Run all checks (build + lint + test)"
    }
}