# {{service_name}}

A {{LANGUAGE}} service with modern architecture.

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
├── model/        # Data models and structures
└── main.{{MAIN_EXT}}       # Entry point
tests/
├── api/          # API tests
└── model/        # Model tests
```

## Getting Started

1. Install dependencies:
   ```bash
   make setup
   ```

2. Run the service:
   ```bash
   make dev
   ```

3. Run tests:
   ```bash
   make test
   ```