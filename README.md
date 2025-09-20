# 🚀 Kickstart

Project scaffolding CLI that generates production-ready applications with best practices and modern tooling.

## Installation

```bash
# Via pip
pip install kickstart-cli

# From source
git clone https://github.com/yourusername/kickstart.git
cd kickstart
poetry install
poetry run kickstart --help
```

## Quick Start

### Create a Python Service (FastAPI)
```bash
kickstart create service my-api --lang python
```

### Add Extensions
```bash
# With PostgreSQL database
kickstart create service my-api --lang python --database postgres

# With Redis cache
kickstart create service my-api --lang python --cache redis

# With JWT authentication
kickstart create service my-api --lang python --auth jwt

# All together
kickstart create service my-api --lang python --database postgres --cache redis --auth jwt
```

### Project Structure (Python Service)
```
my-api/
├── src/
│   ├── main.py              # Application entry point
│   ├── api/                 # Business logic layer
│   ├── model/               # Data layer
│   │   ├── entities/        # Domain models
│   │   ├── dto/             # Data transfer objects
│   │   └── repository/      # Data access patterns
│   ├── routes/              # HTTP routing
│   ├── handler/             # Request handlers
│   ├── clients/             # External service clients
│   └── config/              # Configuration
├── tests/                   # Test suite
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Local development setup
├── requirements.txt         # Python dependencies
├── Makefile                 # Common tasks
└── README.md               # Project documentation
```

## Supported Project Types

### Services (Backend APIs)
```bash
kickstart create service <name> --lang [python|go|rust|cpp]
```
- **Python**: FastAPI by default
- **Go**: Gin framework
- **Rust**: Actix-web
- **C++**: Modern C++20 with CMake

### Frontend Applications
```bash
kickstart create frontend <name>
```
React 18 with TypeScript, Vite, TailwindCSS

### Libraries
```bash
kickstart create lib <name> --lang [python|go|rust]
```

### CLI Tools
```bash
kickstart create cli <name> --lang [python|go|rust]
```

### Monorepo Infrastructure
```bash
kickstart create mono <name> [--helm]
```

## Advanced Usage

### Interactive Mode
```bash
kickstart create
# Follow the prompts
```

### Component Manifest
```yaml
# components.yaml
services:
  - name: user-service
    lang: python
    database: postgres
    auth: jwt

  - name: payment-service
    lang: go
    database: mysql

frontends:
  - name: web-dashboard
```

```bash
kickstart --manifest components.yaml
```

### GitHub Integration
```bash
export GITHUB_TOKEN=your_token_here
kickstart create service my-api --gh
```

### Shell Completion
```bash
# Bash
kickstart completion bash >> ~/.bashrc

# Zsh
kickstart completion zsh >> ~/.zshrc
```

## Development

```bash
# Clone and install
git clone https://github.com/yourusername/kickstart.git
cd kickstart
poetry install

# Run
poetry run kickstart --help

# Test
poetry run pytest

# Type check
poetry run mypy src/

# Lint
poetry run ruff check src/
```