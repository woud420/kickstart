"""Language-specific configuration for template composition."""

from typing import Dict, Any

LANGUAGE_CONFIG: Dict[str, Dict[str, Any]] = {
    "python": {
        "framework": "FastAPI",
        "port": "8000",
        "prerequisites": "- Python 3.11+\n- [uv](https://docs.astral.sh/uv/) for dependency management",
        "commands": "make install       # Install dependencies with uv\nmake dev           # Start development server with hot reload",
        "lint_format": "make lint          # Run linting (ruff + mypy)\nmake format        # Format code (black + ruff)\nmake build         # Build the application",
        "env_example": "DEBUG=true\nLOG_LEVEL=INFO",
        "endpoints": "- `GET /health` - Health check endpoint\n- `GET /docs` - Interactive API documentation",
        "docker_commands": "docker build -t {{SERVICE_NAME}} .\ndocker run -p 8000:8000 {{SERVICE_NAME}}",
        "extra_docs": "\n3. **View API documentation:**\n   - Swagger UI: http://localhost:8000/docs\n   - ReDoc: http://localhost:8000/redoc"
    },
    "rust": {
        "framework": "Actix-web",
        "port": "8000",
        "prerequisites": "- Rust 1.70+ (install via [rustup](https://rustup.rs/))\n- `cargo` package manager",
        "commands": "make install       # Install Rust tools (clippy, rustfmt)\nmake dev           # Start development server with auto-reload\nmake build         # Build release binary",
        "lint_format": "make lint          # Run clippy linting\nmake format        # Format code with rustfmt",
        "env_example": "RUST_LOG=info",
        "endpoints": "- `GET /` - Root endpoint\n- `GET /health` - Health check endpoint",
        "docker_commands": "make docker-build\nmake docker-run",
        "extra_docs": "\n3. **View API endpoints:**\n   - Health check: http://localhost:8000/health"
    },
    "go": {
        "framework": "Gin framework",
        "port": "8000",
        "prerequisites": "- Go 1.22+ (install via [go.dev](https://golang.org/dl/))\n- `go mod` for dependency management",
        "commands": "make install       # Install Go dependencies and tools\nmake dev           # Start development server with auto-reload\nmake build         # Build release binary",
        "lint_format": "make lint          # Run linting (go vet + staticcheck)\nmake format        # Format code (go fmt + goimports)",
        "env_example": "GIN_MODE=debug",
        "endpoints": "- `GET /` - Root endpoint\n- `GET /health` - Health check endpoint",
        "docker_commands": "make docker-build\nmake docker-run",
        "extra_docs": "\n3. **View API endpoints:**\n   - Health check: http://localhost:8000/health"
    },
    "typescript": {
        "framework": "Express.js",
        "port": "8000",
        "prerequisites": "- Node.js 18+ (install via [nodejs.org](https://nodejs.org/))\n- npm or yarn package manager",
        "commands": "make install       # Install dependencies via npm\nmake dev           # Start development server with auto-reload\nmake build         # Build TypeScript to JavaScript\nmake start         # Start production server",
        "lint_format": "make lint          # Run ESLint\nmake format        # Format code with Prettier",
        "env_example": "NODE_ENV=development",
        "endpoints": "- `GET /` - Root endpoint\n- `GET /health` - Health check endpoint",
        "docker_commands": "make docker-build\nmake docker-run",
        "extra_docs": "\n3. **View API endpoints:**\n   - Health check: http://localhost:8000/health"
    },
    "elixir": {
        "framework": "Phoenix",
        "port": "4000",
        "prerequisites": "- Erlang 26.2.5+ and Elixir 1.16.3+\n- [asdf](https://asdf-vm.com/) for version management (recommended)\n- PostgreSQL for database",
        "commands": "make setup-asdf     # First-time setup: install asdf and language versions\nmake install       # Install dependencies\nmake dev           # Start development server with hot reload",
        "lint_format": "make lint          # Run code linting with Credo\nmake format        # Format code with mix format\nmake check         # Run all checks (format, lint, test, dialyzer, security)",
        "env_example": "MIX_ENV=dev\nPHX_SERVER=true",
        "endpoints": "- `GET /health` - Health check endpoint\n- `GET /` - Root endpoint with service information",
        "docker_commands": "docker build -t {{SERVICE_NAME}} .\ndocker run -p 4000:4000 {{SERVICE_NAME}}",
        "extra_docs": "\n3. **View application:**\n   - Health check: http://localhost:4000/health\n   - Root endpoint: http://localhost:4000/"
    }
}

# Handle aliases
LANGUAGE_ALIASES = {
    "ts": "typescript",
    "node": "typescript"
}

def get_language_config(lang: str) -> Dict[str, Any]:
    """Get language configuration, handling aliases."""
    normalized_lang = LANGUAGE_ALIASES.get(lang, lang)
    return LANGUAGE_CONFIG.get(normalized_lang, LANGUAGE_CONFIG["python"])