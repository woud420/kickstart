"""README generation service for different project types."""

from typing import Dict, Any
from src.templates._shared.lang_config import get_language_config


class ReadmeGenerator:
    def __init__(self, project_name: str, language: str):
        self.project_name = project_name
        self.language = language
        self.config = get_language_config(language)
    
    def generate_service_readme(self) -> str:
        """Generate README content for service projects."""
        setup_section = self._get_setup_section()
        
        return f"""# {self.project_name}

A {self.language.title()} service built with {self.config['framework']}.

## Quick Start

### Prerequisites
{self.config['prerequisites']}{setup_section}

## Development Commands

```bash
make help          # Show all available commands
{self.config['commands']}
make test          # Run all tests
make test-watch    # Run tests in watch mode
{self.config['lint_format']}
make clean         # Clean build artifacts
make check         # Run all checks (lint + test)
```

## Configuration

Environment variables can be configured in `.env.example`:

```bash
# Application
APP_NAME={self.project_name}
APP_VERSION=0.1.0
{self.config['env_example']}

# Server
HOST=0.0.0.0
PORT={self.config['port']}

# Add your environment variables here
```

## API Endpoints

{self.config['endpoints']}

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
{self.config['docker_commands']}
```

Or manually:
```bash
docker build -t {self.project_name} .
docker run -p {self.config['port']}:{self.config['port']} {self.project_name}
```"""
    
    def _get_setup_section(self) -> str:
        """Get language-specific setup section."""
        if self.language == "elixir":
            return f"""
### First-Time Setup (Elixir)

If you don't have Erlang/Elixir installed, use asdf for version management:

1. **Setup asdf and language versions:**
   ```bash
   make setup-asdf
   ```
   This will:
   - Install asdf version manager (detects your shell automatically)
   - Install Erlang, Elixir, and Node.js versions from `.tool-versions`
   - Add asdf to your shell profile

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Start development server:**
   ```bash
   make dev
   ```
   The API will be available at http://localhost:{self.config['port']}

3. **View application:**
   - Health check: http://localhost:{self.config['port']}/health
   - Root endpoint: http://localhost:{self.config['port']}/

### Quick Setup (if you already have Elixir)

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Start development server:**
   ```bash
   make dev
   ```
   The API will be available at http://localhost:{self.config['port']}

3. **View application:**
   - Health check: http://localhost:{self.config['port']}/health
   - Root endpoint: http://localhost:{self.config['port']}/"""
        else:
            return f"""
### Development Setup

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Start development server:**
   ```bash
   make dev
   ```
   The API will be available at http://localhost:{self.config['port']}{self.config['extra_docs']}"""
