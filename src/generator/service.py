from pathlib import Path
from typing import Any
import logging
from src.generator.base import BaseGenerator
from src.utils.logger import success, warn
from src.utils.github import create_repo
from src.utils.extension_manager import ExtensionManager
from src.utils.error_handling import (
    safe_operation_context, LanguageNotSupportedError, validate_language_support
)

logger = logging.getLogger(__name__)


class ServiceGenerator(BaseGenerator):
    """Generator for creating microservice projects.
    
    This generator creates a complete microservice project structure with
    language-specific templates, Docker configuration, testing framework,
    and optional Helm charts for Kubernetes deployment.
    
    Attributes:
        lang: Programming language for the service (python, rust, go, cpp)
        gh: Whether to create a GitHub repository
        helm: Whether to include Helm chart scaffolding
        lang_template_dir: Path to language-specific templates
    """
    
    lang: str
    gh: bool
    helm: bool
    database: str | None
    cache: str | None
    auth: str | None
    framework: str | None
    lang_template_dir: Path
    extension_manager: ExtensionManager

    def __init__(
        self,
        name: str,
        lang: str,
        gh: bool,
        config: dict[str, Any],
        helm: bool = False,
        root: str | None = None,
        database: str | None = None,
        cache: str | None = None,
        auth: str | None = None,
        framework: str | None = None
    ) -> None:
        """Initialize the ServiceGenerator.
        
        Args:
            name: Name of the service to create
            lang: Programming language (python, rust, go, cpp)
            gh: Whether to create a GitHub repository
            config: Configuration dictionary with user preferences
            helm: Whether to include Helm chart scaffolding
            root: Root directory for project creation (optional)
            database: Database extension (postgres, mysql, sqlite)
            cache: Cache extension (redis, memcached)
            auth: Authentication extension (jwt, oauth)
            framework: HTTP framework (None for FastAPI default, minimal for standard library)
            
        Raises:
            ValueError: If unsupported language is specified
        """
        super().__init__(name, config, root)
        self.lang = lang
        self.gh = gh
        self.helm = helm
        self.database = database
        self.cache = cache
        self.auth = auth
        self.framework = framework
        self.lang_template_dir = self.template_dir / lang
        self.extension_manager = ExtensionManager()

    def create(self) -> None:
        """Create a complete microservice project.

        This method orchestrates the entire service creation process using the
        standardized create flow from BaseGenerator:
        1. Validates project can be created (directory doesn't exist)
        2. Checks language template availability
        3. Creates directory structure
        4. Writes common template files (README, Dockerfile, etc.)
        5. Sets up language-specific files and dependencies
        6. Creates Helm charts if requested
        7. Optionally creates GitHub repository

        Returns:
            None

        Raises:
            LanguageNotSupportedError: If unsupported language is specified
        """
        # Validate language support
        supported_languages = ["python", "rust", "go", "cpp"]
        validate_language_support(self.lang, supported_languages)

        # Check if templates exist for the language
        if not self.lang_template_dir.exists():
            raise LanguageNotSupportedError(f"No templates found for language: {self.lang}")

        # Define project structure
        directories: list[str] = [
            # New improved structure using src/model/, src/api/, src/routes/, src/handler/, src/clients/
            "src/model", "src/api", "src/routes", "src/handler", "src/clients",
            "src/config",
            "tests/unit/model", "tests/unit/api", "tests/unit/routes",
            "tests/integration/api", "tests/integration/clients",
            "tests/fixtures",
            "docs"
        ]

        # Use template registry for cleaner template management
        template_configs: list[dict[str, str]] = self.template_registry.get_template_configs_for_service(self.lang)

        # Configuration for the common create flow
        architecture_title: str = f"{self.name} Architecture Notes"
        success_message: str = f"{self.lang.title()} service '{self.name}' created successfully in '{self.project}'!"
        def github_create_fn() -> Any:
            return create_repo(self.name) if self.gh else None

        # Execute common create flow with service-specific setup
        success = self.execute_create_flow(
            directories=directories,
            template_configs=template_configs,
            architecture_title=architecture_title,
            success_message=success_message,
            language_setup_fn=self._setup_service_specific,
            additional_setup_fn=self._setup_helm_if_requested,
            github_create_fn=github_create_fn if self.gh else None
        )

        if not success:
            warn(f"Failed to create {self.lang} service '{self.name}'")
    
    def _setup_service_specific(self) -> bool:
        """Setup service-specific files and structure.

        Creates language-specific project files, directory structure,
        and dependency configuration.

        This method dispatches to language-specific setup methods based
        on the configured language.

        Returns:
            True if setup was successful, False otherwise
        """
        with safe_operation_context("Service-specific setup", log_errors=True):
            # Write direct content
            self.write_content(".env.example", "EXAMPLE_ENV_VAR=value\n")

            # Language-specific files and structure
            if self.lang == "python":
                self._create_python_structure()
            elif self.lang == "rust":
                self._create_rust_structure()
            elif self.lang == "cpp":
                self._create_cpp_structure()
            elif self.lang == "go":
                self._create_go_structure()
            else:
                raise LanguageNotSupportedError(f"Unsupported language: {self.lang}")

            return True

    def _setup_helm_if_requested(self) -> bool:
        """Setup Helm charts if requested.

        Returns:
            True if Helm setup was successful or not requested, False if failed
        """
        if not self.helm:
            return True

        with safe_operation_context("Helm chart creation", log_errors=True):
            self._create_helm_chart()
            return True

    def _create_python_structure(self) -> None:
        """Create Python-specific project structure.

        Sets up a Python microservice with:
        - FastAPI framework by default (modern, async, type-safe)
        - Minimal http.server framework when --framework minimal is used
        - Optional extensions (database, cache, auth) via progressive enhancement
        - Clean architecture with proper separation of concerns
        - Type hints and proper error handling
        """
        # Create __init__.py files for all Python packages
        python_packages = [
            "src", "src/model", "src/api", "src/routes", "src/handler", "src/clients", "src/config",
            "tests", "tests/unit", "tests/unit/model", "tests/unit/api", "tests/unit/routes",
            "tests/integration", "tests/integration/api", "tests/integration/clients",
            "tests/fixtures"
        ]
        
        for package_path in python_packages:
            self.write_content(f"{package_path}/__init__.py", "")
        
        # Choose templates based on framework
        if self.framework == "minimal":
            # Use minimal HTTP server framework (standard library only)
            core_templates = [
                # Core application files
                ("src/main.py", "python/extensions/minimal/core/main.py.tpl"),

                # Minimal requirements (standard library only)
                ("requirements.txt", "python/extensions/minimal/core/requirements.txt.tpl"),
            ]
        else:
            # Use FastAPI framework (default)
            core_templates = [
                # Core application files
                ("src/main.py", "python/core/main.py.tpl"),

                # Model layer (all data-related code)
                ("src/model/__init__.py", "python/core/model/__init__.py.tpl"),
                ("src/model/entities.py", "python/core/model/entities.py.tpl"),
                ("src/model/dto.py", "python/core/model/dto.py.tpl"),
                ("src/model/repository.py", "python/core/model/repository.py.tpl"),

                # API layer (business logic)
                ("src/api/__init__.py", "python/core/api/__init__.py.tpl"),
                ("src/api/services.py", "python/core/api/services.py.tpl"),

                # Routes layer (HTTP routing)
                ("src/routes/__init__.py", "python/core/routes/__init__.py.tpl"),
                ("src/routes/users.py", "python/core/routes/users.py.tpl"),
                ("src/routes/health.py", "python/core/routes/health.py.tpl"),

                # Configuration
                ("src/config/__init__.py", "python/core/config/__init__.py.tpl"),
                ("src/config/settings.py", "python/core/config/settings.py.tpl"),

                # Core requirements (FastAPI by default)
                ("requirements.txt", "python/core/requirements.txt.tpl"),
            ]
        
        for target_path, template_path in core_templates:
            self.write_template(target_path, template_path)
        
        # Add extensions based on flags (only for FastAPI framework)
        if self.framework != "minimal":
            self._add_python_extensions()
        
        # Create environment example
        self.write_content(".env.example", """# Application Settings
APP_NAME={{service_name}}
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database Settings (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME={{service_name}}_db

# Redis Settings (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Security Settings
SECRET_KEY=your_secret_key_here_at_least_32_characters_long
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
EMAIL_ENABLED=false
EMAIL_BACKEND=console

# Feature Flags
FEATURE_USER_REGISTRATION=true
FEATURE_EMAIL_NOTIFICATIONS=false
""")
        
        # Create basic migration file as example
        self.write_content("migrations/001_initial.sql", """-- Initial database schema
-- This is an example migration file

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    profile_data JSONB DEFAULT '{}'::jsonb
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
""")
        
        self.create_directories(["migrations"])

    def _add_python_extensions(self) -> None:
        """Add extension functionality based on flags.

        This method uses ExtensionManager to add database, cache, and authentication
        extensions based on the flags provided during initialization.
        """
        # Apply extensions using the extension manager
        extensions_added, all_extension_requirements = self.extension_manager.apply_extensions(
            writer=self,
            database=self.database,
            cache=self.cache,
            auth=self.auth
        )

        # Update requirements.txt with extensions
        if all_extension_requirements:
            extension_requirements = "\n\n# Extension requirements\n" + "\n".join(all_extension_requirements) + "\n"

            # Read core requirements and append extensions
            try:
                with open(self.project / "requirements.txt", "r") as f:
                    current_requirements = f.read()
                enhanced_requirements = current_requirements + extension_requirements
                self.write_content("requirements.txt", enhanced_requirements)
            except FileNotFoundError:
                # If core requirements don't exist, create with extensions only
                self.write_content("requirements.txt", "\n".join(all_extension_requirements))

        # Log what was added
        if extensions_added:
            from src.utils.logger import success
            success(f"Extensions added: {', '.join(extensions_added)}")


    def _create_rust_structure(self) -> None:
        """Create Rust-specific project structure.
        
        Sets up a Rust microservice with:
        - mod.rs files for module organization
        - Actix-web-based main.rs with basic HTTP server
        - Cargo.toml with common dependencies
        - Proper crate structure
        """
        # Create mod.rs files
        for dir_path in ["src/api", "src/model", "tests/api", "tests/model"]:
            self.write_content(f"{dir_path}/mod.rs", "// Module definitions\n")

        # Create minimal main file
        self.write_content("src/main.rs", "use actix_web::{web, App, HttpResponse, HttpServer};\n\n#[actix_web::main]\nasync fn main() -> std::io::Result<()> {\n    HttpServer::new(|| {\n        App::new()\n            .route(\"/\", web::get().to(|| async { HttpResponse::Ok().json(\"Hello World\") }))\n    })\n    .bind(\"127.0.0.1:8080\")?\n    .run()\n    .await\n}\n")

        # Create Cargo.toml
        self.write_template("Cargo.toml", "rust/Cargo.toml.tpl")

    def _create_cpp_structure(self) -> None:
        """Create C++-specific project structure.
        
        Sets up a C++ microservice with:
        - Header files with proper namespace organization
        - Basic main.cpp with console output
        - CMakeLists.txt for build configuration
        - Modern C++ project structure
        """
        # Create minimal header files
        self.write_content("src/api/routes.hpp", "#pragma once\n\nnamespace api {\n    class Routes {\n    public:\n        Routes() = default;\n    };\n}\n")
        self.write_content("src/model/user.hpp", "#pragma once\n\nnamespace model {\n    // Add your models here\n}\n")
        
        # Create minimal main file
        self.write_content("src/main.cpp", "#include <iostream>\n\nint main() {\n    std::cout << \"Hello World\" << std::endl;\n    return 0;\n}\n")

        # Create CMakeLists.txt
        self.write_template("CMakeLists.txt", "cpp/CMakeLists.txt.tpl")

    def _create_go_structure(self) -> None:
        """Create Go-specific project structure.
        
        Sets up a Go microservice with:
        - main.go with basic HTTP server using net/http
        - go.mod file for module definition
        - .gitkeep files for empty directories
        - Standard Go project layout
        """
        # Create minimal files
        self.write_content("src/api/.gitkeep", "")
        self.write_content("src/model/.gitkeep", "")
        self.write_content("tests/api/.gitkeep", "")
        self.write_content("tests/model/.gitkeep", "")

        # Create main.go
        self.write_content(
            "src/main.go",
            """package main

import (
    "fmt"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, `{"message": "Hello World"}`)
    })
    fmt.Println("Listening on :8080...")
    http.ListenAndServe(":8080", nil)
}
"""
        )
        # go.mod
        self.write_template("go.mod", "go/go.mod.tpl")

    def _create_helm_chart(self) -> None:
        """Create Helm chart structure and files.
        
        Generates a complete Helm chart for Kubernetes deployment including:
        - Chart.yaml with metadata
        - values.yaml with default configuration
        - deployment.yaml template for application deployment
        - Proper Helm chart directory structure
        
        The chart is created in helm/{service_name}/ directory.
        """
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


