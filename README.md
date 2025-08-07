# 🚀 Kickstart v0.2.1

The first public release of **Kickstart**, an opinionated scaffolding tool for full-stack projects with strong infra and CI/CD support.

## ✨ Features

**Project Types:**
- 🔧 **Backend Services** - Python, Rust, Elixir, Go, TypeScript, C++
- 🖥️ **Frontend Apps** - React with TypeScript  
- 📦 **Libraries & CLIs** - Reusable packages and command-line tools
- 🏗️ **Infrastructure Monorepos** - Complete platform setup with K8s/Docker

**Built-in Tooling:**
- 🛠️ Makefiles, Docker, CI/CD, testing setup, documentation
- ⚙️ ASDF integration with automatic shell detection (Elixir)
- 🤖 AI integration via MCP for Claude and other models
- 🔄 Self-updating and shell completion

## 📦 Installation

```bash
curl -L https://github.com/woud420/kickstart/releases/download/v0.2.1/kickstart -o /usr/local/bin/kickstart
chmod +x /usr/local/bin/kickstart
```

## 🚀 Quick Start

```bash
# Backend service with any language
kickstart create service my-api --lang python --gh
kickstart create service my-api --lang elixir --gh  # Includes ASDF setup
kickstart create service my-api --lang rust --gh

# React frontend
kickstart create frontend my-app --gh

# Infrastructure monorepo  
kickstart create mono my-platform --helm

# Library or CLI tool
kickstart create lib my-utils --lang python
kickstart create cli my-tool --lang python
```

**What you get:** Full project structure, Docker, CI/CD, testing, documentation, and deployment configs.

## 🔧 Advanced Usage

**Interactive Mode:**
```bash
kickstart create  # Guided wizard
```

**Batch Generation:**
```bash
kickstart --manifest components.md  # Generate multiple projects from manifest
```

**Shell Completion:**
```bash
kickstart completion zsh >> ~/.zshrc
kickstart upgrade  # Self-update
```

**GitHub Integration:** Set `GITHUB_TOKEN` environment variable for automatic repo creation with `--gh`.

## 🤖 AI Integration

Kickstart includes MCP (Model Context Protocol) support for AI models like Claude.

```bash
make mcp-setup  # Install dependencies
make mcp-test   # Test the server
```

Configure Claude Desktop to use kickstart directly. See [`tools/mcp-server/README.md`](tools/mcp-server/README.md) for details.

## 🏗️ Architecture

Kickstart uses a modular, extensible architecture:

- **Strategy Pattern**: Each language (Python, Elixir, etc.) has its own strategy class
- **Mixins**: Common functionality (GitHub, templates) shared across generators  
- **Centralized Config**: Language settings in one place for easy maintenance

### Adding New Languages

```python
# 1. Add to lang_config.py
LANGUAGE_CONFIG["kotlin"] = {"framework": "Spring Boot", ...}

# 2. Create strategy class  
class KotlinStrategy(LanguageStrategy):
    def create_structure(self): # implementation

# 3. Register it
LANGUAGE_STRATEGIES["kotlin"] = KotlinStrategy
```

**Recent improvements:** 83% code reduction, eliminated duplication, maintained full compatibility.

## 🧪 Development

```bash
make tests     # Run all tests
make build     # Build binary
make package   # Package for distribution
```

**Contributing:** The modular architecture makes it easy to add languages, extend generators, or improve templates. See the [Architecture](#-architecture) section for guidance.
