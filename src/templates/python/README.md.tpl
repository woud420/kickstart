# {{ service_name }}

A Python service with FastAPI (or a `--framework minimal` standard-library HTTP server).

## Development

```bash
# Run the service
make dev

# Run tests
make test

# Build the wheel
make build

# Lint, typecheck, and test together
make check
```

Other canonical targets: `make fmt`, `make format-check`, `make typecheck`, `make docker-build`.

## Project Structure

```
src/
├── api/          # FastAPI route registration helpers
├── config/       # Settings and environment parsing
├── model/        # Data models, DTOs, and repositories
└── routes/       # HTTP route handlers
tests/            # Pytest suite
```

The service listens on `PORT` and defaults to `8080`.
