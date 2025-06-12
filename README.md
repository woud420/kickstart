# 🚀 Kickstart v0.2.1

The first public release of **Kickstart**, an opinionated scaffolding tool for full-stack projects with strong infra and CI/CD support.

## ✨ Features

- 🔧 Create structured **backend services** (`python`, `rust`, `ts-node`, `cpp`)
- 🖥️ Generate modern **frontend apps** (React/TS)
- 📦 Define **libraries** and **CLI tools** as standalone modules
- 🏗️ Spin up an entire **infrastructure monorepo**:
  - Kustomize overlays OR Helm charts (via `--helm`)
  - Docker Compose for local dev
  - Terraform for cloud provisioning
  - GitHub Actions for CI/CD pipelines
- 🛠️ Built-in **Makefiles**, `.gitignore`, `.env.example`, `README.md`, `architecture/`
- 🧪 Supports unit, integration, and e2e test layout
- 📦 Package as a **single binary** using `shiv`
- 🔄 Self-updating with `kickstart upgrade`
- 🔁 Shell autocompletion with `kickstart completion [bash|zsh]`

## 📦 Installation

```bash
curl -L https://github.com/woud420/kickstart/releases/download/v0.2.1/kickstart -o /usr/local/bin/kickstart
chmod +x /usr/local/bin/kickstart
```

## 🚀 Quick Start Examples

### 1. Frontend Project
Create a modern React/TypeScript frontend application:

```bash
kickstart create frontend my-awesome-app --root ./projects
```

This will generate:
- React + TypeScript setup
- Vite as the build tool
- ESLint and Prettier configuration
- Jest for testing
- GitHub Actions workflow for CI/CD

### 2. Backend Service
Create a Python backend service with infrastructure support:

```bash
kickstart create service user-service --lang python --root ./services --gh --helm
```

This will generate:
- FastAPI/Flask project structure
- Dockerfile and docker-compose.yml
- Helm chart for Kubernetes deployment
- GitHub Actions workflow
- Unit and integration test setup
- Makefile with common commands

Project structure:
```
user-service/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── models.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   └── services/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_routes.py
│   │   └── test_models.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── test_config.py
│   └── services/
│       └── __init__.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── Makefile
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

### 2.1 Rust Service
Create a Rust backend service with infrastructure support:

```bash
kickstart create service payment-service --lang rust --root ./services --gh --helm
```

This will generate:
- Rust project with Cargo.toml
- Actix-web or Rocket.rs setup
- Dockerfile and docker-compose.yml
- Helm chart for Kubernetes deployment
- GitHub Actions workflow
- Unit and integration test setup
- Makefile with common commands

Project structure:
```
payment-service/
├── src/
│   ├── main.rs
│   ├── api/
│   │   ├── mod.rs
│   │   ├── routes.rs
│   │   └── models.rs
│   ├── core/
│   │   ├── mod.rs
│   │   └── config.rs
│   └── services/
│       └── mod.rs
├── tests/
│   ├── api/
│   │   ├── mod.rs
│   │   ├── routes_test.rs
│   │   └── models_test.rs
│   ├── core/
│   │   ├── mod.rs
│   │   └── config_test.rs
│   └── services/
│       └── mod.rs
├── Cargo.toml
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

### 2.2 C++ Service
Create a C++ backend service with infrastructure support:

```bash
kickstart create service compute-service --lang cpp --root ./services --gh --helm
```

This will generate:
- CMake-based project structure
- Modern C++ setup (C++17/20)
- Dockerfile and docker-compose.yml
- Helm chart for Kubernetes deployment
- GitHub Actions workflow
- Unit and integration test setup
- Makefile with common commands

Project structure:
```
compute-service/
├── src/
│   ├── main.cpp
│   ├── api/
│   │   ├── routes.hpp
│   │   └── models.hpp
│   ├── core/
│   │   ├── config.hpp
│   │   └── config.cpp
│   └── services/
│       └── service.hpp
├── tests/
│   ├── api/
│   │   ├── routes_test.cpp
│   │   └── models_test.cpp
│   ├── core/
│   │   └── config_test.cpp
│   └── services/
│       └── service_test.cpp
├── CMakeLists.txt
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

### 3. Infrastructure Monorepo
Create a complete infrastructure setup for a microservices architecture:

```bash
kickstart create mono my-platform --root ./platform --helm
```

This will generate a monorepo structure with:
```
platform/
├── apps/
│   ├── frontend/          # React frontend
│   ├── auth-service/      # Authentication service
│   └── api-service/       # Main API service
├── infra/
│   ├── k8s/              # Kubernetes manifests
│   ├── terraform/        # Cloud infrastructure
│   └── docker-compose/   # Local development
└── .github/
    └── workflows/        # CI/CD pipelines
```

### 4. Library Package
Create a reusable library:

```bash
kickstart create lib my-utils --lang python --root ./libs
```

This will generate:
- Python package structure
- Poetry for dependency management
- Unit test setup
- Documentation template
- GitHub Actions workflow

### 5. CLI Tool
Create a command-line tool:

```bash
kickstart create cli my-cli --lang python --root ./tools
```

This will generate:
- CLI project structure
- Click or Typer setup
- Argument parsing
- Command structure
- Unit tests
- GitHub Actions workflow

## 🔧 Advanced Usage

### Interactive Mode
If you prefer a guided experience, run without arguments:

```bash
kickstart create
```

This will launch an interactive wizard to help you create your project.
The wizard will prompt for the project type, name, root directory and other options.

### Shell Completion
Enable shell completion for better CLI experience:

```bash
# For zsh
kickstart completion zsh >> ~/.zshrc

# For bash
kickstart completion bash >> ~/.bashrc
```

### Self-Updating
Keep your Kickstart installation up to date:

```bash
kickstart upgrade
```

## 📄 Component Manifest
Kickstart supports describing multiple components in a single Markdown file. The
manifest can live anywhere; pass the file to the CLI when running Kickstart.

### Keys
- `name` – component identifier (services and frontends)
- `root` – directory where the component is created
- `lang` – optional language for a service. Kickstart chooses a default when
  omitted.

### Example manifest
```markdown
## services
- name: user-service
  lang: python
  root: services/user-service

## frontends
- name: dashboard
  root: apps/dashboard

## monorepo
- root: platform
```

Run `kickstart --manifest path/to/components.md` to generate everything listed.

### GitHub Integration
To automatically create a remote repository when using `--gh`, set the
`GITHUB_TOKEN` environment variable with a personal access token that has `repo`
permissions before running `kickstart create`.
