# {{SERVICE_NAME}}

A Go service using idiomatic project structure.

## Development

```bash
# Run the service
go run ./src/main.go

# Run tests
go test ./...

# Build
go build -o bin/{{SERVICE_NAME}} ./src
```

## Project Structure

```
src/
├── api/          # API endpoints and handlers
├── model/        # Data models and structures
└── main.go       # Entry point
tests/
├── api/          # API tests
└── model/        # Model tests
``` 