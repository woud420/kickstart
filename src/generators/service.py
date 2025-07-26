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
        self.write_template("README.md", f"{self.lang}/README.md.tpl")
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

        # Helm chart if requested
        if self.helm:
            self._create_helm_chart()

        self.log_success(f"{self.lang.title()} service '{self.name}' created successfully in '{self.project}'!")

        if self.gh:
            create_repo(self.name)

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
        
        # Create .env.example from template
        self.write_template(".env.example", "python/env.example.tpl")

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
        
        # Create .env.example from template
        self.write_template(".env.example", "rust/env.example.tpl")
        
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
        
        # Create .env.example from template
        self.write_template(".env.example", "go/env.example.tpl")
        
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
        
        # Create .env.example from template
        self.write_template(".env.example", "typescript/env.example.tpl")
        
        # Create test file
        self.write_template("tests/index.test.ts", "typescript/index.test.ts.tpl")

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


