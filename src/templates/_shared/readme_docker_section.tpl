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