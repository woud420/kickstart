"""Configuration for template generation with shared patterns."""

from pathlib import Path

class TemplateConfig:
    """Language-specific configuration for template generation."""
    
    LANGUAGE_CONFIGS = {
        "python": {
            "default_port": "8000",
            "description": "A Python service built with FastAPI.",
            "prerequisites": "- Python 3.11+\n- [uv](https://docs.astral.sh/uv/) for dependency management",
            "lang_env_vars": "DEBUG=true\nLOG_LEVEL=INFO",
            "commands": [
                "make install       # Install dependencies with uv",
                "make dev           # Start development server with hot reload", 
                "make build         # Build the application",
                "make test          # Run all tests",
                "make test-watch    # Run tests in watch mode",
                "make lint          # Run linting (ruff + mypy)",
                "make format        # Format code (black + ruff)",
                "make clean         # Clean build artifacts",
                "make check         # Run all checks (lint + test)"
            ]
        },
        "rust": {
            "default_port": "8000", 
            "description": "A Rust service built with Actix-web.",
            "prerequisites": "- Rust 1.70+ (install via [rustup](https://rustup.rs/))\n- `cargo` package manager",
            "lang_env_vars": "RUST_LOG=info",
            "commands": [
                "make install       # Install Rust tools (clippy, rustfmt)",
                "make dev           # Start development server with auto-reload",
                "make build         # Build release binary", 
                "make test          # Run all tests",
                "make test-watch    # Run tests in watch mode",
                "make lint          # Run clippy linting",
                "make format        # Format code with rustfmt",
                "make clean         # Clean build artifacts",
                "make check         # Run all checks (lint + test)"
            ]
        },
        "go": {
            "default_port": "8000",
            "description": "A Go service built with Gin framework.",
            "prerequisites": "- Go 1.22+ (install via [go.dev](https://golang.org/dl/))\n- `go mod` for dependency management", 
            "lang_env_vars": "GIN_MODE=debug",
            "commands": [
                "make install       # Install Go dependencies and tools",
                "make dev           # Start development server with auto-reload",
                "make build         # Build release binary",
                "make test          # Run all tests", 
                "make test-watch    # Run tests in watch mode",
                "make lint          # Run linting (go vet + staticcheck)",
                "make format        # Format code (go fmt + goimports)",
                "make clean         # Clean build artifacts",
                "make check         # Run all checks (lint + test)"
            ]
        },
        "typescript": {
            "default_port": "8000",
            "description": "A TypeScript service built with Express.js.",
            "prerequisites": "- Node.js 18+ (install via [nodejs.org](https://nodejs.org/))\n- npm or yarn package manager",
            "lang_env_vars": "NODE_ENV=development",
            "commands": [
                "make install       # Install dependencies via npm",
                "make dev           # Start development server with auto-reload",
                "make build         # Build TypeScript to JavaScript",
                "make start         # Start production server",
                "make test          # Run tests with Jest",
                "make test-watch    # Run tests in watch mode", 
                "make lint          # Run ESLint",
                "make format        # Format code with Prettier",
                "make clean         # Clean build artifacts",
                "make check         # Run all checks (build + lint + test)"
            ]
        }
    }
    
    @classmethod
    def get_vars(cls, lang: str, service_name: str) -> dict:
        """Get template variables for a specific language."""
        config = cls.LANGUAGE_CONFIGS.get(lang, {})
        
        return {
            "service_name": service_name,
            "default_port": config.get("default_port", "8000"),
            "description": config.get("description", "A service"),
            "prerequisites": config.get("prerequisites", ""),
            "lang_env_vars": config.get("lang_env_vars", ""),
            "command_list": "\n".join(config.get("commands", []))
        }
    
    @classmethod
    def get_shared_env_template(cls) -> str:
        """Get shared environment template."""
        return """# Application Configuration
APP_NAME={{SERVICE_NAME}}
APP_VERSION=0.1.0
{{LANG_ENV_VARS}}

# Server Configuration
HOST=0.0.0.0
PORT={{DEFAULT_PORT}}

# Database Configuration (if needed)
# DATABASE_URL=postgresql://user:password@localhost:5432/{{SERVICE_NAME}}_db

# Redis Configuration (if needed)
# REDIS_URL=redis://localhost:6379/0

# API Keys and Secrets
# SECRET_KEY=your-secret-key-here
# JWT_SECRET_KEY=your-jwt-secret-key-here

# External Services
# EXTERNAL_API_URL=https://api.example.com
# EXTERNAL_API_KEY=your-api-key-here

# Monitoring and Logging
# SENTRY_DSN=your-sentry-dsn-here
# ENABLE_METRICS=true

# Development
# ENABLE_CORS=true"""
