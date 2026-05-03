# {{service_name}}

A Rust service with Actix-web.

## Development

```bash
# Run the service
make dev

# Run tests
make test

# Build
make build

# Lint
make lint
```

## Project Structure

```
src/
├── api/          # API endpoints and routes
├── clients/      # Optional generated service clients
└── model/        # Data models and structures
tests/
├── api/          # API tests
└── model/        # Model tests
```
