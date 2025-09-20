# 🚀 Kickstart

A powerful, opinionated project scaffolding CLI that generates production-ready applications with best practices, modern tooling, and comprehensive CI/CD pipelines.

[![CI](https://github.com/yourusername/kickstart/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/kickstart/actions/workflows/ci.yml)
[![Release](https://github.com/yourusername/kickstart/actions/workflows/release.yml/badge.svg)](https://github.com/yourusername/kickstart/actions/workflows/release.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

### Core Capabilities
- 🎯 **Smart Project Generation** - Create backend services, frontend apps, libraries, and CLI tools with a single command
- 🏗️ **Modern Architecture** - Built-in support for clean architecture with proper separation of concerns
- 🔌 **Progressive Enhancement** - Start minimal, add features as needed (database, cache, auth)
- 📦 **Multi-Language Support** - Python (FastAPI), Go, Rust, C++, TypeScript
- 🐳 **Container-First** - Every project includes optimized Dockerfiles and docker-compose configs
- ☸️ **Kubernetes Ready** - Optional Helm charts for production deployments
- 🔄 **CI/CD Pipelines** - GitHub Actions workflows for testing, building, and releasing
- 📝 **Intelligent Templates** - Jinja2-powered templates with inheritance to eliminate duplication

### Recent Improvements (v0.3.0)
- ✅ **FastAPI as Default** - Modern async Python framework as the default choice
- ✅ **Template Inheritance** - 70% reduction in template duplication using Jinja2
- ✅ **Extension System** - Modular architecture for database, cache, and auth extensions
- ✅ **Error Handling** - Standardized error handling utilities across the codebase
- ✅ **Python 3.12+** - Support for latest Python features and performance improvements
- ✅ **Binary Releases** - Automated binary builds for Linux, macOS, and Windows

## 📦 Installation

### Via pip (Recommended)
```bash
pip install kickstart-cli
```

### Via pipx (Isolated Environment)
```bash
pipx install kickstart-cli
```

### Via Homebrew (macOS/Linux)
```bash
brew tap yourusername/kickstart
brew install kickstart
```

### Via Binary Release
Download the latest binary for your platform from [Releases](https://github.com/yourusername/kickstart/releases):

```bash
# macOS
curl -L https://github.com/yourusername/kickstart/releases/latest/download/kickstart-darwin-x86_64.tar.gz | tar xz
sudo mv kickstart /usr/local/bin/

# Linux
curl -L https://github.com/yourusername/kickstart/releases/latest/download/kickstart-linux-x86_64.tar.gz | tar xz
sudo mv kickstart /usr/local/bin/

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/yourusername/kickstart/releases/latest/download/kickstart-windows-x86_64.zip" -OutFile kickstart.zip
Expand-Archive kickstart.zip -DestinationPath .
```

### Via Docker
```bash
docker run -v $(pwd):/workspace ghcr.io/yourusername/kickstart create service my-app
```

### From Source
```bash
git clone https://github.com/yourusername/kickstart.git
cd kickstart
poetry install
poetry run kickstart --help
```

## 🚀 Quick Start

### Create a Python Service (FastAPI)
```bash
kickstart create service my-api --lang python
```

This generates a production-ready FastAPI service with:
- ✅ Clean architecture (model/api/routes/handler layers)
- ✅ Health checks and monitoring endpoints
- ✅ Structured logging with structlog
- ✅ Docker and docker-compose setup
- ✅ Comprehensive error handling
- ✅ Type hints throughout

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
│   │   ├── __init__.py
│   │   └── services.py      # Service implementations
│   ├── model/               # Data layer
│   │   ├── __init__.py
│   │   ├── entities/        # Domain models
│   │   ├── dto/             # Data transfer objects
│   │   └── repository/      # Data access patterns
│   ├── routes/              # HTTP routing
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   └── users.py         # User endpoints (with auth)
│   ├── handler/             # Request handlers
│   │   ├── __init__.py
│   │   └── auth.py          # Authentication handler (with JWT)
│   ├── clients/             # External service clients
│   │   └── __init__.py
│   └── config/              # Configuration
│       └── settings.py      # Pydantic settings
├── tests/                   # Test suite
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Local development setup
├── requirements.txt         # Python dependencies
├── Makefile                 # Common tasks
├── README.md               # Project documentation
└── .github/
    └── workflows/
        └── ci.yml          # CI/CD pipeline
```

## 🎯 Supported Project Types

### Services (Backend APIs)
```bash
kickstart create service <name> --lang [python|go|rust|cpp]
```

**Python**: FastAPI by default, minimal HTTP server option
**Go**: Gin framework with clean architecture
**Rust**: Actix-web with async support
**C++**: Modern C++20 with CMake

### Frontend Applications
```bash
kickstart create frontend <name>
```
- React 18 with TypeScript
- Vite for fast builds
- TailwindCSS for styling
- Jest & React Testing Library
- ESLint & Prettier configured

### Libraries
```bash
kickstart create lib <name> --lang [python|go|rust]
```
- Proper package structure
- Unit test setup
- Documentation templates
- CI/CD for publishing

### CLI Tools
```bash
kickstart create cli <name> --lang [python|go|rust]
```
- Argument parsing (Typer for Python, Cobra for Go)
- Command structure
- Shell completion support
- Binary distribution setup

### Monorepo Infrastructure
```bash
kickstart create mono <name> [--helm]
```
Complete platform setup with:
- Multiple services
- Frontend applications
- Kubernetes manifests (or Helm charts)
- Terraform modules
- Docker Compose for local dev
- Shared CI/CD pipelines

## 🛠️ Advanced Features

### Interactive Mode
Launch the interactive wizard for guided project creation:
```bash
kickstart create
# Follow the prompts
```

### Component Manifest
Define multiple components in a YAML or Markdown file:

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

  - name: mobile-app
```

```bash
kickstart --manifest components.yaml
```

### GitHub Integration
Automatically create GitHub repositories:
```bash
export GITHUB_TOKEN=your_token_here
kickstart create service my-api --gh
```

### Shell Completion
Enable tab completion for better CLI experience:
```bash
# Bash
kickstart completion bash >> ~/.bashrc

# Zsh
kickstart completion zsh >> ~/.zshrc

# Fish
kickstart completion fish > ~/.config/fish/completions/kickstart.fish
```

## 🏗️ Architecture Decisions

### Why FastAPI as Default?
- **Performance**: One of the fastest Python frameworks
- **Developer Experience**: Automatic API documentation, type hints
- **Modern**: Built on modern Python features (async/await, type hints)
- **Production Ready**: Used by Microsoft, Netflix, Uber

### Template System
- **Jinja2 Templates**: Industry-standard templating with inheritance
- **Progressive Enhancement**: Start simple, add complexity as needed
- **No Lock-in**: Generated code is yours to modify

### Extension Philosophy
- **Composition Over Configuration**: Extensions are additive, not transformative
- **Zero to Production**: Every combination produces a working application
- **Best Practices**: Each extension follows established patterns

## 🧪 Development

### Prerequisites
- Python 3.12+
- Poetry 1.7+
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/kickstart.git
cd kickstart

# Install dependencies
poetry install

# Run the CLI
poetry run kickstart --help

# Run tests
poetry run pytest

# Type checking
poetry run mypy src/

# Linting
poetry run ruff check src/
```

### Project Structure
```
kickstart/
├── src/
│   ├── cli/                 # CLI interface (Typer)
│   ├── generator/           # Project generators
│   ├── templates/           # Jinja2 templates
│   └── utils/              # Utilities and helpers
├── tests/                  # Test suite
├── .github/workflows/      # CI/CD pipelines
└── pyproject.toml         # Project configuration
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Guide
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`poetry run pytest`)
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [Cookiecutter](https://github.com/cookiecutter/cookiecutter)
- Template system powered by [Jinja2](https://jinja.palletsprojects.com/)
- CLI interface built with [Typer](https://typer.tiangolo.com/)
- Rich terminal output via [Rich](https://rich.readthedocs.io/)

## 📊 Stats

- **Templates**: 100+ production-ready templates
- **Languages**: 5 supported languages
- **Extensions**: 10+ optional extensions
- **Code Reduction**: 70% less boilerplate with template inheritance
- **Active Development**: Regular updates and improvements

---

Built with ❤️ by the Kickstart team. Happy scaffolding! 🚀