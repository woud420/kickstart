# {{SERVICE_NAME}}

A Go service built with Gin framework.

## Quick Start

### Prerequisites
- Go 1.22+ (install via [go.dev](https://golang.org/dl/))
- `go mod` for dependency management

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

3. **View API endpoints:**
   - Health check: http://localhost:8000/health

## Development Commands

```bash
make help          # Show all available commands
make install       # Install Go dependencies and tools
make dev           # Start development server with auto-reload
make build         # Build release binary
make test          # Run all tests
make test-watch    # Run tests in watch mode
make lint          # Run linting (go vet + staticcheck)
make format        # Format code (go fmt + goimports)
make clean         # Clean build artifacts
make check         # Run all checks (lint + test)
```

## Project Structure

```
{{SERVICE_NAME}}/
├── cmd/
│   └── main.go              # Application entry point
├── internal/
│   ├── api/                 # API routes and handlers
│   ├── model/               # Data models and business logic
│   └── config/              # Configuration management
├── pkg/                     # Public packages (if any)
├── tests/                   # Test files
│   ├── api/
│   └── model/
├── go.mod                   # Go module definition
├── go.sum                   # Dependency checksums
├── Makefile                # Development commands
└── README.md               # This file
```

## Configuration

Environment variables can be configured in `.env.example`:

```bash
# Application
APP_NAME={{SERVICE_NAME}}
APP_VERSION=0.1.0
GIN_MODE=debug

# Server
HOST=0.0.0.0
PORT=8000

# Add your environment variables here
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

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
make docker-build
make docker-run
```

Or manually:
```bash
docker build -t {{SERVICE_NAME}} .
docker run -p 8000:8000 {{SERVICE_NAME}}
``` 