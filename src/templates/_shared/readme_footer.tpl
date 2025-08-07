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
docker run -p {{DEFAULT_PORT}}:{{DEFAULT_PORT}} {{SERVICE_NAME}}
```
