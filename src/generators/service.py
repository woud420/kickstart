from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator
from src.utils.logger import success, warn
from src.utils.github import create_repo

class ServiceGenerator(BaseGenerator):
    def __init__(self, name: str, lang: str, gh: bool, config: dict, helm: bool = False, root: Optional[str] = None):
        super().__init__(name, config, root)
        self.lang = lang
        self.gh = gh
        self.helm = helm
        self.lang_template_dir = self.template_dir / lang

    def create(self) -> None:
        if not self.create_project():
            return

        if not self.lang_template_dir.exists():
            warn(f"No templates for language: {self.lang}")
            return

        # Create basic directories (language-specific structure created later)
        self.create_directories(["architecture"])
        self.create_architecture_docs(f"{self.name} Architecture Notes")

        # Write common template files
        self._create_readme()
        self.write_template(".gitignore", f"{self.lang}/gitignore.tpl")
        self.write_template("Dockerfile", f"{self.lang}/Dockerfile.tpl")
        self.write_template("Makefile", f"{self.lang}/Makefile.tpl")
        

        # Language-specific files and structure
        if self.lang == "python":
            self._create_python_structure()
        elif self.lang == "rust":
            self._create_rust_structure()
        elif self.lang == "cpp":
            self._create_cpp_structure()
        elif self.lang == "go":
            self._create_go_structure()
        elif self.lang in ["typescript", "ts", "node"]:
            self._create_typescript_structure()
        elif self.lang == "elixir":
            self._create_elixir_structure()

        # Helm chart if requested
        if self.helm:
            self._create_helm_chart()

        self.log_success(f"{self.lang.title()} service '{self.name}' created successfully in '{self.project}'!")

        if self.gh:
            create_repo(self.name)

    def _create_readme(self) -> None:
        """Create README.md using shared template with language-specific content."""
        lang_configs = {
            "python": {
                "framework": "FastAPI",
                "prerequisites": "- Python 3.11+\n- [uv](https://docs.astral.sh/uv/) for dependency management",
                "commands": "make install       # Install dependencies with uv\nmake dev           # Start development server with hot reload",
                "lint_format": "make lint          # Run linting (ruff + mypy)\nmake format        # Format code (black + ruff)\nmake build         # Build the application",
                "env_example": "DEBUG=true\nLOG_LEVEL=INFO",
                "endpoints": "- `GET /health` - Health check endpoint\n- `GET /docs` - Interactive API documentation",
                "docker_commands": "docker build -t {{SERVICE_NAME}} .\ndocker run -p 8000:8000 {{SERVICE_NAME}}",
                "extra_docs": "\n3. **View API documentation:**\n   - Swagger UI: http://localhost:8000/docs\n   - ReDoc: http://localhost:8000/redoc"
            },
            "rust": {
                "framework": "Actix-web",
                "prerequisites": "- Rust 1.70+ (install via [rustup](https://rustup.rs/))\n- `cargo` package manager",
                "commands": "make install       # Install Rust tools (clippy, rustfmt)\nmake dev           # Start development server with auto-reload\nmake build         # Build release binary",
                "lint_format": "make lint          # Run clippy linting\nmake format        # Format code with rustfmt",
                "env_example": "RUST_LOG=info",
                "endpoints": "- `GET /` - Root endpoint\n- `GET /health` - Health check endpoint",
                "docker_commands": "make docker-build\nmake docker-run",
                "extra_docs": "\n3. **View API endpoints:**\n   - Health check: http://localhost:8000/health"
            },
            "go": {
                "framework": "Gin framework",
                "prerequisites": "- Go 1.22+ (install via [go.dev](https://golang.org/dl/))\n- `go mod` for dependency management",
                "commands": "make install       # Install Go dependencies and tools\nmake dev           # Start development server with auto-reload\nmake build         # Build release binary",
                "lint_format": "make lint          # Run linting (go vet + staticcheck)\nmake format        # Format code (go fmt + goimports)",
                "env_example": "GIN_MODE=debug",
                "endpoints": "- `GET /` - Root endpoint\n- `GET /health` - Health check endpoint",
                "docker_commands": "make docker-build\nmake docker-run",
                "extra_docs": "\n3. **View API endpoints:**\n   - Health check: http://localhost:8000/health"
            },
            "typescript": {
                "framework": "Express.js",
                "prerequisites": "- Node.js 18+ (install via [nodejs.org](https://nodejs.org/))\n- npm or yarn package manager",
                "commands": "make install       # Install dependencies via npm\nmake dev           # Start development server with auto-reload\nmake build         # Build TypeScript to JavaScript\nmake start         # Start production server",
                "lint_format": "make lint          # Run ESLint\nmake format        # Format code with Prettier",
                "env_example": "NODE_ENV=development",
                "endpoints": "- `GET /` - Root endpoint\n- `GET /health` - Health check endpoint",
                "docker_commands": "make docker-build\nmake docker-run",
                "extra_docs": "\n3. **View API endpoints:**\n   - Health check: http://localhost:8000/health"
            },
            "elixir": {
                "framework": "Phoenix",
                "prerequisites": "- Erlang 26.2.5+ and Elixir 1.16.3+\n- [asdf](https://asdf-vm.com/) for version management (recommended)\n- PostgreSQL for database",
                "commands": "make setup-asdf     # First-time setup: install asdf and language versions\nmake install       # Install dependencies\nmake dev           # Start development server with hot reload",
                "lint_format": "make lint          # Run code linting with Credo\nmake format        # Format code with mix format\nmake check         # Run all checks (format, lint, test, dialyzer, security)",
                "env_example": "MIX_ENV=dev\nPHX_SERVER=true",
                "endpoints": "- `GET /health` - Health check endpoint\n- `GET /` - Root endpoint with service information",
                "docker_commands": "docker build -t {{SERVICE_NAME}} .\ndocker run -p 4000:4000 {{SERVICE_NAME}}",
                "extra_docs": "\n3. **View application:**\n   - Health check: http://localhost:4000/health\n   - Root endpoint: http://localhost:4000/"
            }
        }
        
        # Handle typescript/ts/node aliases
        lang_key = "typescript" if self.lang in ["typescript", "ts", "node"] else self.lang
        config = lang_configs.get(lang_key, lang_configs["python"])
        
        # Special handling for Elixir to include asdf setup
        setup_section = ""
        if self.lang == "elixir":
            port = "4000"
            setup_section = """
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
   The API will be available at http://localhost:4000

3. **View application:**
   - Health check: http://localhost:4000/health
   - Root endpoint: http://localhost:4000/

### Quick Setup (if you already have Elixir)

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Start development server:**
   ```bash
   make dev
   ```
   The API will be available at http://localhost:4000

3. **View application:**
   - Health check: http://localhost:4000/health
   - Root endpoint: http://localhost:4000/"""
        else:
            port = "8000"
            setup_section = f"""
### Development Setup

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Start development server:**
   ```bash
   make dev
   ```
   The API will be available at http://localhost:{port}{config['extra_docs']}"""
        
        readme_content = f"""# {{{{SERVICE_NAME}}}}

A {self.lang.title()} service built with {config['framework']}.

## Quick Start

### Prerequisites
{config['prerequisites']}{setup_section}

## Development Commands

```bash
make help          # Show all available commands
{config['commands']}
make test          # Run all tests
make test-watch    # Run tests in watch mode
{config['lint_format']}
make clean         # Clean build artifacts
make check         # Run all checks (lint + test)
```

## Configuration

Environment variables can be configured in `.env.example`:

```bash
# Application
APP_NAME={{{{SERVICE_NAME}}}}
APP_VERSION=0.1.0
{config['env_example']}

# Server
HOST=0.0.0.0
PORT=8000

# Add your environment variables here
```

## API Endpoints

{config['endpoints']}

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
{config['docker_commands']}
```

Or manually:
```bash
docker build -t {{{{SERVICE_NAME}}}} .
docker run -p 8000:8000 {{{{SERVICE_NAME}}}}
```"""

        # Write to a temporary shared template file and then use write_template
        import tempfile
        import os
        
        # Create temporary file for the generated README template
        temp_readme_path = self.template_dir / "_shared" / "readme_generated.tpl"
        temp_readme_path.write_text(readme_content)
        
        # Use write_template to handle variable substitution
        self.write_template("README.md", "_shared/readme_generated.tpl")
        
        # Clean up temporary file
        temp_readme_path.unlink()

    def _create_python_structure(self) -> None:
        """Create Python-specific project structure."""
        # Create Python project directories
        self.create_directories([
            "src", "src/api", "src/model", 
            "tests", "tests/api", "tests/model"
        ])
        
        # Create __init__.py files
        for dir_path in ["src", "src/api", "src/model", "tests", "tests/api", "tests/model"]:
            self.write_content(f"{dir_path}/__init__.py", "")

        # Create main FastAPI app from template
        self.write_template("src/main.py", "python/main.py.tpl")
        
        # Create pyproject.toml from template
        self.write_template("pyproject.toml", "python/pyproject.toml.tpl")
        
        # Create .env.example from shared template
        self.write_template(".env.example", "_shared/env.example.tpl", 
                          language_specific_env="DEBUG=true\nLOG_LEVEL=INFO", 
                          default_port="8000")

        # Create requirements.txt (for compatibility, though uv uses pyproject.toml)
        self.write_template("requirements.txt", "python/requirements.txt.tpl")
        
        # Create test file
        self.write_template("tests/test_main.py", "python/test_main.py.tpl")

    def _create_rust_structure(self) -> None:
        """Create Rust-specific project structure."""
        # Create Rust project directories
        self.create_directories([
            "src", "src/api", "src/model", 
            "tests", "tests/api", "tests/model"
        ])
        
        # Create mod.rs files
        for dir_path in ["src/api", "src/model", "tests/api", "tests/model"]:
            self.write_content(f"{dir_path}/mod.rs", "// Module definitions\n")

        # Create main Actix-web app from template
        self.write_template("src/main.rs", "rust/main.rs.tpl")
        
        # Create Cargo.toml from template
        self.write_template("Cargo.toml", "rust/Cargo.toml.tpl")
        
        # Create .env.example from shared template
        self.write_template(".env.example", "_shared/env.example.tpl",
                          language_specific_env="RUST_LOG=info",
                          default_port="8000")
        
        # Create test file
        self.write_template("tests/main_test.rs", "rust/main_test.rs.tpl")

    def _create_cpp_structure(self) -> None:
        """Create C++-specific project structure."""
        # Create minimal header files
        self.write_content("src/api/routes.hpp", "#pragma once\n\nnamespace api {\n    class Routes {\n    public:\n        Routes() = default;\n    };\n}\n")
        self.write_content("src/model/user.hpp", "#pragma once\n\nnamespace model {\n    // Add your models here\n}\n")
        
        # Create minimal main file
        self.write_content("src/main.cpp", "#include <iostream>\n\nint main() {\n    std::cout << \"Hello World\" << std::endl;\n    return 0;\n}\n")

        # Create CMakeLists.txt
        self.write_template("CMakeLists.txt", "cpp/CMakeLists.txt.tpl")

    def _create_go_structure(self) -> None:
        """Create Go-specific project structure."""
        # Create Go project directories (following Go standard layout)
        self.create_directories([
            "cmd",
            "internal/api",
            "internal/model", 
            "internal/config",
            "pkg",
            "tests/api",
            "tests/model"
        ])

        # Create main.go from template  
        self.write_template("cmd/main.go", "go/main.go.tpl")
        
        # Create go.mod from template
        self.write_template("go.mod", "go/go.mod.tpl")
        
        # Create .env.example from shared template
        self.write_template(".env.example", "_shared/env.example.tpl",
                          language_specific_env="GIN_MODE=debug", 
                          default_port="8000")
        
        # Create test file
        self.write_template("cmd/main_test.go", "go/main_test.go.tpl")

    def _create_typescript_structure(self) -> None:
        """Create TypeScript/Node.js-specific project structure."""
        # Create project directories
        self.create_directories([
            "src/routes",
            "src/middleware", 
            "src/types",
            "src/utils",
            "tests/routes",
            "tests/utils"
        ])

        # Create main application file
        self.write_template("src/index.ts", "typescript/index.ts.tpl")
        
        # Create package.json and config files
        self.write_template("package.json", "typescript/package.json.tpl")
        self.write_template("tsconfig.json", "typescript/tsconfig.json.tpl")
        self.write_template("jest.config.js", "typescript/jest.config.js.tpl")
        self.write_template(".eslintrc.js", "typescript/eslintrc.js.tpl")
        self.write_template(".prettierrc", "typescript/prettierrc.tpl")
        
        # Create .env.example from shared template
        self.write_template(".env.example", "_shared/env.example.tpl",
                          language_specific_env="NODE_ENV=development",
                          default_port="8000")
        
        # Create test file
        self.write_template("tests/index.test.ts", "typescript/index.test.ts.tpl")

    def _create_elixir_structure(self) -> None:
        """Create Elixir/Phoenix-specific project structure."""
        # Create Elixir project directories following Phoenix conventions
        self.create_directories([
            "lib", f"lib/{self.name}", f"lib/{self.name}_web",
            f"lib/{self.name}_web/controllers", 
            "config", 
            "priv/repo/migrations",
            "priv/repo",
            "test", "test/support",
            f"test/{self.name}",
            f"test/{self.name}_web",
            f"test/{self.name}_web/controllers"
        ])
        
        # Helper function to convert service name to different cases
        def to_pascal_case(name):
            return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))
        
        def to_snake_case(name):
            return name.replace('-', '_').lower()
        
        pascal_name = to_pascal_case(self.name)
        snake_name = to_snake_case(self.name)
        
        # Create main application files
        self.write_template("mix.exs", "elixir/mix.exs.tpl", 
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create lib structure
        self.write_template(f"lib/{snake_name}/application.ex", "elixir/application.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template(f"lib/{snake_name}/repo.ex", "elixir/repo.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create web structure
        self.write_template(f"lib/{snake_name}_web.ex", "elixir/service_web.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template(f"lib/{snake_name}_web/endpoint.ex", "elixir/endpoint.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template(f"lib/{snake_name}_web/router.ex", "elixir/router.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create controllers
        self.write_template(f"lib/{snake_name}_web/controllers/health_controller.ex", 
                          "elixir/health_controller.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template(f"lib/{snake_name}_web/controllers/root_controller.ex", 
                          "elixir/root_controller.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create config files
        self.write_template("config/config.exs", "elixir/config.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template("config/dev.exs", "elixir/dev.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template("config/test.exs", "elixir/test.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create .env.example from shared template
        self.write_template(".env.example", "_shared/env.example.tpl",
                          language_specific_env="MIX_ENV=dev\nPHX_SERVER=true",
                          default_port="4000")
        
        # Create .tool-versions for asdf
        self.write_template(".tool-versions", "elixir/tool-versions.tpl")
        
        # Create test files
        self.write_template("test/test_helper.exs", "elixir/test_helper.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template("test/support/conn_case.ex", "elixir/conn_case.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template("test/support/data_case.ex", "elixir/data_case.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create controller tests
        self.write_template(f"test/{snake_name}_web/controllers/health_controller_test.exs",
                          "elixir/health_controller_test.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.write_template(f"test/{snake_name}_web/controllers/root_controller_test.exs",
                          "elixir/root_controller_test.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)

    def _create_helm_chart(self) -> None:
        """Create Helm chart structure and files."""
        helm_path = self.project / "helm" / self.name
        self.create_directories([str(helm_path / "templates")])

        # Write Helm chart files
        for file, template in {
            "Chart.yaml": "monorepo/helm/Chart.yaml",
            "values.yaml": "monorepo/helm/values.yaml",
            "templates/deployment.yaml": "monorepo/helm/deployment.yaml"
        }.items():
            self.write_template(f"helm/{self.name}/{file}", template)

        success("Helm chart scaffolded")


