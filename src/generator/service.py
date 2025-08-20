from pathlib import Path
from typing import Any
from src.generator.base import BaseGenerator
from src.utils.logger import success, warn
from src.utils.github import create_repo


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
    lang_template_dir: Path
    
    def __init__(
        self, 
        name: str, 
        lang: str, 
        gh: bool, 
        config: dict[str, Any], 
        helm: bool = False, 
        root: str | None = None
    ) -> None:
        """Initialize the ServiceGenerator.
        
        Args:
            name: Name of the service to create
            lang: Programming language (python, rust, go, cpp)
            gh: Whether to create a GitHub repository
            config: Configuration dictionary with user preferences
            helm: Whether to include Helm chart scaffolding
            root: Root directory for project creation (optional)
            
        Raises:
            ValueError: If unsupported language is specified
        """
        super().__init__(name, config, root)
        self.lang = lang
        self.gh = gh
        self.helm = helm
        self.lang_template_dir = self.template_dir / lang

    def create(self) -> None:
        """Create a complete microservice project.
        
        This method orchestrates the entire service creation process:
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
            OSError: If file/directory operations fail
            TemplateError: If template rendering fails
        """
        # Check if project can be created
        if not self.create_project():
            return

        # Check if templates exist for the language
        if not self.lang_template_dir.exists():
            warn(f"No templates for language: {self.lang}")
            return

        directories: list[str] = [
            "src", "src/api", "src/model", 
            "tests", "tests/api", "tests/model",
            "architecture"
        ]
        
        # Use template registry for cleaner template management
        template_configs: list[dict[str, str]] = self.template_registry.get_template_configs_for_service(self.lang)
        
        architecture_title: str = f"{self.name} Architecture Notes"
        success_message: str = f"{self.lang.title()} service '{self.name}' created successfully in '{self.project}'!"
        
        github_create_fn = lambda: create_repo(self.name) if self.gh else None
        
        # Create project structure without the create_project check since we already did it
        self.init_basic_structure(directories)
        
        # Write template files
        self.write_templates_from_config(template_configs)
        
        # Create architecture docs
        self.create_architecture_docs(architecture_title)

        # Language-specific setup
        self._setup_service_specific()

        # Success message and GitHub integration
        self.create_with_github(success_message, github_create_fn if self.gh else None)
    
    def _setup_service_specific(self) -> None:
        """Setup service-specific files and structure.
        
        Creates language-specific project files, directory structure,
        and dependency configuration. Also sets up Helm charts if requested.
        
        This method dispatches to language-specific setup methods based
        on the configured language.
        """
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

        # Helm chart if requested
        if self.helm:
            self._create_helm_chart()

    def _create_python_structure(self) -> None:
        """Create Python-specific project structure.
        
        Sets up a Python microservice with:
        - __init__.py files for proper package structure
        - FastAPI-based main.py with basic endpoint
        - requirements.txt with common dependencies
        - Proper directory structure for src and tests
        """
        # Create __init__.py files
        for dir_path in ["src", "src/api", "src/model", "tests", "tests/api", "tests/model"]:
            self.write_content(f"{dir_path}/__init__.py", "")

        # Create minimal main file
        self.write_content("src/main.py", "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello World'}\n")

        # Create requirements.txt
        self.write_template("requirements.txt", "python/requirements.txt.tpl")

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


