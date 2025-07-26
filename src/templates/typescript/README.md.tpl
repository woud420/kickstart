# {{SERVICE_NAME}}

A TypeScript service built with Express.js.

## Quick Start

### Prerequisites
- Node.js 18+ (install via [nodejs.org](https://nodejs.org/))
- npm or yarn package manager

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
make install       # Install dependencies via npm
make dev           # Start development server with auto-reload
make build         # Build TypeScript to JavaScript
make start         # Start production server
make test          # Run tests with Jest
make test-watch    # Run tests in watch mode
make lint          # Run ESLint
make format        # Format code with Prettier
make clean         # Clean build artifacts
make check         # Run all checks (build + lint + test)
```

## Project Structure

```
{{SERVICE_NAME}}/
├── src/
│   ├── index.ts             # Application entry point
│   ├── routes/              # API routes
│   │   └── health.ts
│   ├── middleware/          # Express middleware
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts
│   └── utils/               # Utility functions
├── dist/                    # Compiled JavaScript (generated)
├── tests/                   # Test files
│   ├── routes/
│   └── utils/
├── package.json             # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── jest.config.js          # Jest test configuration
├── .eslintrc.js            # ESLint configuration
├── .prettierrc             # Prettier configuration
├── Makefile               # Development commands
└── README.md              # This file
```

## Configuration

Environment variables can be configured in `.env.example`:

```bash
# Application
APP_NAME={{SERVICE_NAME}}
APP_VERSION=0.1.0
NODE_ENV=development

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

## Production

Build and start production server:
```bash
make build
make start
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