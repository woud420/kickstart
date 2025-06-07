from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator
from src.utils.logger import success, warn

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

        # Create project structure
        self.create_directories([
            "src",
            "src/api",
            "src/model",
            "tests",
            "tests/api",
            "tests/model",
            "architecture"
        ])

        # Write common template files
        self.write_template("README.md", f"{self.lang}/README.md.tpl")
        self.write_template(".gitignore", f"{self.lang}/gitignore.tpl")
        self.write_template("Dockerfile", f"{self.lang}/Dockerfile.tpl")
        self.write_template("Makefile", f"{self.lang}/Makefile.tpl")
        
        # Write direct content
        self.write_content("architecture/README.md", f"# {self.name} Architecture Notes\n")
        self.write_content(".env.example", "EXAMPLE_ENV_VAR=value\n")

        # Language-specific files and structure
        if self.lang == "python":
            self._create_python_structure()
        elif self.lang == "rust":
            self._create_rust_structure()
        elif self.lang == "cpp":
            self._create_cpp_structure()

        # Helm chart if requested
        if self.helm:
            self._create_helm_chart()

        self.log_success(f"{self.lang.title()} service '{self.name}' created successfully in '{self.project}'!")

    def _create_python_structure(self) -> None:
        """Create Python-specific project structure."""
        # Create __init__.py files
        for dir_path in ["src", "src/api", "src/model", "tests", "tests/api", "tests/model"]:
            self.write_content(f"{dir_path}/__init__.py", "")

        # Create minimal main file
        self.write_content("src/main.py", "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello World'}\n")

        # Create requirements.txt
        self.write_template("requirements.txt", "python/requirements.txt.tpl")

    def _create_rust_structure(self) -> None:
        """Create Rust-specific project structure."""
        # Create mod.rs files
        for dir_path in ["src/api", "src/model", "tests/api", "tests/model"]:
            self.write_content(f"{dir_path}/mod.rs", "// Module definitions\n")

        # Create minimal main file
        self.write_content("src/main.rs", "use actix_web::{web, App, HttpResponse, HttpServer};\n\n#[actix_web::main]\nasync fn main() -> std::io::Result<()> {\n    HttpServer::new(|| {\n        App::new()\n            .route(\"/\", web::get().to(|| async { HttpResponse::Ok().json(\"Hello World\") }))\n    })\n    .bind(\"127.0.0.1:8080\")?\n    .run()\n    .await\n}\n")

        # Create Cargo.toml
        self.write_template("Cargo.toml", "rust/Cargo.toml.tpl")

    def _create_cpp_structure(self) -> None:
        """Create C++-specific project structure."""
        # Create minimal header files
        self.write_content("src/api/routes.hpp", "#pragma once\n\nnamespace api {\n    class Routes {\n    public:\n        Routes() = default;\n    };\n}\n")
        self.write_content("src/model/user.hpp", "#pragma once\n\nnamespace model {\n    // Add your models here\n}\n")
        
        # Create minimal main file
        self.write_content("src/main.cpp", "#include <iostream>\n\nint main() {\n    std::cout << \"Hello World\" << std::endl;\n    return 0;\n}\n")

        # Create CMakeLists.txt
        self.write_template("CMakeLists.txt", "cpp/CMakeLists.txt.tpl")

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

def create_service(name: str, lang: str, gh: bool, config: dict, helm: bool = False, root: str = None):
    """Factory function for backward compatibility"""
    generator = ServiceGenerator(name, lang, gh, config, helm, root)
    generator.create()

