# Project Structure

This project follows a standard service architecture:

## Directory Layout

```
├── src/                 # Source code
│   ├── api/            # API endpoints and routes  
│   ├── model/          # Data models and business logic
│   └── main.*          # Application entry point
├── tests/              # Test files
│   ├── api/            # API integration tests
│   └── model/          # Unit tests for models
├── architecture/       # Architecture documentation
├── Dockerfile         # Container configuration
├── Makefile          # Build and development commands
└── README.md         # Project documentation
```

## Development Workflow

1. **Setup**: `make setup` - Install dependencies
2. **Development**: `make dev` - Run in development mode
3. **Testing**: `make test` - Run test suite
4. **Building**: `make build` - Create production build
5. **Linting**: `make lint` - Code quality checks

## Architecture Patterns

- **API Layer**: HTTP endpoints and request handling
- **Model Layer**: Business logic and data structures
- **Clean Architecture**: Dependencies point inward
- **Testing**: Comprehensive unit and integration tests