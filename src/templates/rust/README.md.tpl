# {{SERVICE_NAME}}

A Rust service built with Actix-web.

## Quick Start

### Prerequisites
- Rust 1.70+ (install via [rustup](https://rustup.rs/))
- `cargo` package manager

### Development Setup

1. **Install development tools:**
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
make install       # Install Rust tools (clippy, rustfmt)
make dev           # Start development server with auto-reload
make build         # Build release binary
make test          # Run all tests
make test-watch    # Run tests in watch mode
make lint          # Run clippy linting
make format        # Format code with rustfmt
make clean         # Clean build artifacts
make check         # Run all checks (lint + test)
```

## Project Structure

```
{{SERVICE_NAME}}/
├── src/
│   ├── main.rs              # Application entry point
│   ├── api/                 # API routes and handlers
│   │   └── mod.rs
│   └── model/               # Data models and business logic
│       └── mod.rs
├── tests/                   # Test files mirror src/ structure
│   ├── api/
│   └── model/
├── Cargo.toml              # Project dependencies and metadata
├── Makefile               # Development commands
└── README.md              # This file
```

## Configuration

Environment variables can be configured in `.env.example`:

```bash
# Application
APP_NAME={{SERVICE_NAME}}
APP_VERSION=0.1.0
RUST_LOG=info

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