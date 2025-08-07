# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Dependencies
- `make setup` or `make install` - Set up virtual environment and install dependencies
- `make venv` - Create virtual environment only

### Building and Running
- `make build` - Build self-contained kickstart binary (creates symlink in repo root)
- `make run` - Run kickstart CLI from virtual environment
- `make package` - Package poetry project for distribution

### Testing
- `make tests` - Run all pytest tests (requires build step first)
- Individual test files can be run with: `pytest tests/unit/path/to/test_file.py`
- Integration tests: `pytest tests/integration/`

### Utilities
- `make shell` - Drop into Poetry shell for interactive development
- `make clean` - Remove virtual environment and build artifacts

## Project Architecture

### Core Components
- **CLI Entry Point**: `src/cli/main.py` - Main Typer application with commands for create, version, upgrade, completion
- **Generators**: `src/generators/` - Project scaffolding generators for different project types:
  - `base.py` - BaseGenerator class with common functionality for all generators
  - `service.py` - Backend service generation (Python, Rust, C++, TypeScript)
  - `frontend.py` - React frontend generation
  - `lib.py` - Library package generation
  - `monorepo.py` - Infrastructure monorepo generation
- **Templates**: `src/templates/` - Template files organized by project type (python/, rust/, react/, etc.)
- **Utilities**: `src/utils/` - Common utilities (config, filesystem, GitHub, logging, updater)
- **API Layer**: `src/api.py` - High-level functions called by CLI commands

### Project Generation Flow
1. CLI commands in `main.py` parse arguments and call functions in `api.py`
2. API functions instantiate appropriate generator classes from `src/generators/`
3. Generators use `BaseGenerator` methods to create directories and render templates
4. Templates are populated with project-specific variables and written to target locations

### Key Features
- **Multi-language support**: Python, Rust, C++, TypeScript/Node.js for services
- **Infrastructure scaffolding**: Kubernetes (Helm/Kustomize), Docker, Terraform, GitHub Actions
- **Interactive mode**: Wizard-style project creation when no arguments provided
- **GitHub integration**: Automatic repository creation with `--gh` flag
- **Self-updating**: Built-in upgrade mechanism via `kickstart upgrade`

### Template System
Templates use `.tpl` extension and support variable substitution. Key variables:
- `service_name` - Project name
- Language-specific variables passed from generators
- Templates are organized by project type in `src/templates/`

### Testing Structure
- **Unit tests**: `tests/unit/` - Test individual components and utilities
- **Integration tests**: `tests/integration/` - End-to-end CLI testing using actual kickstart binary
- Integration tests use `sys.executable` to run `kickstart.py` directly

### Code Generation Features
- **Multi-Language DAO Generation**: `kickstart codegen schema.sql --lang [rust|cpp|python|go]`
- **Rust**: Complete trait/implementation/mock pattern with SQLx integration
- **C++**: Modern C++17 interfaces with nlohmann/json and pqxx support
- **Python**: Pydantic models with SQLAlchemy async DAOs and validation schemas
- **Go**: Interfaces with sqlx implementations and proper struct tags
- **Repository Pattern**: Automatically creates interfaces, implementations, and test-friendly mocks

### Dependencies
- **Typer**: CLI framework with rich terminal output
- **Rich**: Terminal formatting and prompts
- **Poetry**: Dependency management and packaging
- **Requests**: HTTP client for GitHub API and updates

### Enhanced Templates
- **Sophisticated Makefiles**: Color-coded output, comprehensive commands, dependency detection
- **Database Integration**: Built-in SQLx support with migration commands
- **Modern Tooling**: Automatic package manager detection (bun/npm), development shortcuts
