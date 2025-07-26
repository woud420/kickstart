# {{SERVICE_NAME}}

A Python service built with FastAPI.

## Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Development Setup

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Start development server:**
   ```bash
   make dev
   ```
   The API will be available at http://localhost:8000

3. **View API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Development Commands

```bash
make help          # Show all available commands
make install       # Install dependencies with uv
make dev           # Start development server with hot reload
make test          # Run all tests
make test-watch    # Run tests in watch mode
make lint          # Run linting (ruff + mypy)
make format        # Format code (black + ruff)
make build         # Build the application
make clean         # Clean build artifacts
make check         # Run all checks (lint + test)
```

## Project Structure

```
{{SERVICE_NAME}}/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/                 # API routes and models
│   │   └── __init__.py
│   └── model/               # Data models and business logic
│       └── __init__.py
├── tests/                   # Test files mirror src/ structure
│   ├── api/
│   └── model/
├── pyproject.toml          # Project dependencies and configuration
├── Makefile               # Development commands
└── README.md              # This file
```

## Configuration

Environment variables can be configured in `.env.example`:

```bash
# Application
APP_NAME={{SERVICE_NAME}}
APP_VERSION=0.1.0
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Add your environment variables here
```

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

## Testing

Run tests with:
```bash
make test
```

For development with auto-rerun:
```bash
make test-watch
```

## Docker

Build and run with Docker:
```bash
docker build -t {{SERVICE_NAME}} .
docker run -p 8000:8000 {{SERVICE_NAME}}
```
