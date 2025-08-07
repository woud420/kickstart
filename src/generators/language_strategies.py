"""Language-specific project structure strategies."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol


class GeneratorProtocol(Protocol):
    """Protocol for generator classes that use language strategies."""
    name: str
    project: Path
    template_dir: Path
    
    def create_directories(self, directories: list[str]) -> None: ...
    def write_content(self, target: str, content: str) -> None: ...
    def write_template(self, target: str, template_path: str, **kwargs) -> None: ...


class LanguageStrategy(ABC):
    """Abstract base class for language-specific project structure strategies."""
    
    def __init__(self, generator: GeneratorProtocol):
        self.generator = generator
    
    @abstractmethod
    def create_structure(self) -> None:
        """Create language-specific project structure."""
        pass


class PythonStrategy(LanguageStrategy):
    """Python project structure strategy."""
    
    def create_structure(self) -> None:
        # Create Python project directories
        self.generator.create_directories([
            "src", "src/api", "src/model", 
            "tests", "tests/api", "tests/model"
        ])
        
        # Create __init__.py files
        for dir_path in ["src", "src/api", "src/model", "tests", "tests/api", "tests/model"]:
            self.generator.write_content(f"{dir_path}/__init__.py", "")

        # Create main FastAPI app from template
        self.generator.write_template("src/main.py", "python/main.py.tpl")
        
        # Create pyproject.toml from template
        self.generator.write_template("pyproject.toml", "python/pyproject.toml.tpl")
        
        # Create .env.example from shared template
        self.generator.write_template(".env.example", "_shared/env.example.tpl", 
                          language_specific_env="DEBUG=true\nLOG_LEVEL=INFO", 
                          default_port="8000")

        # Create requirements.txt (for compatibility, though uv uses pyproject.toml)
        self.generator.write_template("requirements.txt", "python/requirements.txt.tpl")
        
        # Create test file
        self.generator.write_template("tests/test_main.py", "python/test_main.py.tpl")


class RustStrategy(LanguageStrategy):
    """Rust project structure strategy."""
    
    def create_structure(self) -> None:
        # Create Rust project directories
        self.generator.create_directories([
            "src", "src/api", "src/model", 
            "tests", "tests/api", "tests/model"
        ])
        
        # Create mod.rs files
        for dir_path in ["src/api", "src/model", "tests/api", "tests/model"]:
            self.generator.write_content(f"{dir_path}/mod.rs", "// Module definitions\n")

        # Create main Actix-web app from template
        self.generator.write_template("src/main.rs", "rust/main.rs.tpl")
        
        # Create Cargo.toml from template
        self.generator.write_template("Cargo.toml", "rust/Cargo.toml.tpl")
        
        # Create .env.example from shared template
        self.generator.write_template(".env.example", "_shared/env.example.tpl",
                          language_specific_env="RUST_LOG=info",
                          default_port="8000")
        
        # Create test file
        self.generator.write_template("tests/main_test.rs", "rust/main_test.rs.tpl")


class GoStrategy(LanguageStrategy):
    """Go project structure strategy."""
    
    def create_structure(self) -> None:
        # Create Go project directories (following Go standard layout)
        self.generator.create_directories([
            "cmd",
            "internal/api",
            "internal/model", 
            "internal/config",
            "pkg",
            "tests/api",
            "tests/model"
        ])

        # Create main.go from template  
        self.generator.write_template("cmd/main.go", "go/main.go.tpl")
        
        # Create go.mod from template
        self.generator.write_template("go.mod", "go/go.mod.tpl")
        
        # Create .env.example from shared template
        self.generator.write_template(".env.example", "_shared/env.example.tpl",
                          language_specific_env="GIN_MODE=debug", 
                          default_port="8000")
        
        # Create test file
        self.generator.write_template("cmd/main_test.go", "go/main_test.go.tpl")


class TypeScriptStrategy(LanguageStrategy):
    """TypeScript/Node.js project structure strategy."""
    
    def create_structure(self) -> None:
        # Create project directories
        self.generator.create_directories([
            "src/routes",
            "src/middleware", 
            "src/types",
            "src/utils",
            "tests/routes",
            "tests/utils"
        ])

        # Create main application file
        self.generator.write_template("src/index.ts", "typescript/index.ts.tpl")
        
        # Create package.json and config files
        self.generator.write_template("package.json", "typescript/package.json.tpl")
        self.generator.write_template("tsconfig.json", "typescript/tsconfig.json.tpl")
        self.generator.write_template("jest.config.js", "typescript/jest.config.js.tpl")
        self.generator.write_template(".eslintrc.js", "typescript/eslintrc.js.tpl")
        self.generator.write_template(".prettierrc", "typescript/prettierrc.tpl")
        
        # Create .env.example from shared template
        self.generator.write_template(".env.example", "_shared/env.example.tpl",
                          language_specific_env="NODE_ENV=development",
                          default_port="8000")
        
        # Create test file
        self.generator.write_template("tests/index.test.ts", "typescript/index.test.ts.tpl")


class ElixirStrategy(LanguageStrategy):
    """Elixir/Phoenix project structure strategy."""
    
    def create_structure(self) -> None:
        # Create Elixir project directories following Phoenix conventions
        snake_name = self._to_snake_case(self.generator.name)
        
        self.generator.create_directories([
            "lib", f"lib/{snake_name}", f"lib/{snake_name}_web",
            f"lib/{snake_name}_web/controllers", 
            "config", 
            "priv/repo/migrations",
            "priv/repo",
            "test", "test/support",
            f"test/{snake_name}",
            f"test/{snake_name}_web",
            f"test/{snake_name}_web/controllers"
        ])
        
        pascal_name = self._to_pascal_case(self.generator.name)
        
        # Create main application files
        self.generator.write_template("mix.exs", "elixir/mix.exs.tpl", 
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create lib structure
        self.generator.write_template(f"lib/{snake_name}/application.ex", "elixir/application.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template(f"lib/{snake_name}/repo.ex", "elixir/repo.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create web structure
        self.generator.write_template(f"lib/{snake_name}_web.ex", "elixir/service_web.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template(f"lib/{snake_name}_web/endpoint.ex", "elixir/endpoint.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template(f"lib/{snake_name}_web/router.ex", "elixir/router.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create controllers
        self.generator.write_template(f"lib/{snake_name}_web/controllers/health_controller.ex", 
                          "elixir/health_controller.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template(f"lib/{snake_name}_web/controllers/root_controller.ex", 
                          "elixir/root_controller.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create config files
        self.generator.write_template("config/config.exs", "elixir/config.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template("config/dev.exs", "elixir/dev.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template("config/test.exs", "elixir/test.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create .env.example from shared template
        self.generator.write_template(".env.example", "_shared/env.example.tpl",
                          language_specific_env="MIX_ENV=dev\nPHX_SERVER=true",
                          default_port="4000")
        
        # Create .tool-versions for asdf
        self.generator.write_template(".tool-versions", "elixir/tool-versions.tpl")
        
        # Create test files
        self.generator.write_template("test/test_helper.exs", "elixir/test_helper.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template("test/support/conn_case.ex", "elixir/conn_case.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template("test/support/data_case.ex", "elixir/data_case.ex.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        # Create controller tests
        self.generator.write_template(f"test/{snake_name}_web/controllers/health_controller_test.exs",
                          "elixir/health_controller_test.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
        
        self.generator.write_template(f"test/{snake_name}_web/controllers/root_controller_test.exs",
                          "elixir/root_controller_test.exs.tpl",
                          SERVICE_NAME_PASCAL=pascal_name,
                          SERVICE_NAME_UNDERSCORE=snake_name)
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert service name to PascalCase."""
        return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))
    
    def _to_snake_case(self, name: str) -> str:
        """Convert service name to snake_case."""
        return name.replace('-', '_').lower()


class CppStrategy(LanguageStrategy):
    """C++ project structure strategy."""
    
    def create_structure(self) -> None:
        # Create minimal header files
        self.generator.write_content("src/api/routes.hpp", "#pragma once\n\nnamespace api {\n    class Routes {\n    public:\n        Routes() = default;\n    };\n}\n")
        self.generator.write_content("src/model/user.hpp", "#pragma once\n\nnamespace model {\n    // Add your models here\n}\n")
        
        # Create minimal main file
        self.generator.write_content("src/main.cpp", "#include <iostream>\n\nint main() {\n    std::cout << \"Hello World\" << std::endl;\n    return 0;\n}\n")

        # Create CMakeLists.txt
        self.generator.write_template("CMakeLists.txt", "cpp/CMakeLists.txt.tpl")


# Strategy factory
LANGUAGE_STRATEGIES = {
    "python": PythonStrategy,
    "rust": RustStrategy,
    "go": GoStrategy,
    "typescript": TypeScriptStrategy,
    "ts": TypeScriptStrategy,
    "node": TypeScriptStrategy,
    "elixir": ElixirStrategy,
    "cpp": CppStrategy,
}


def get_language_strategy(language: str, generator: GeneratorProtocol) -> LanguageStrategy:
    """Get the appropriate language strategy for the given language."""
    strategy_class = LANGUAGE_STRATEGIES.get(language)
    if not strategy_class:
        raise ValueError(f"Unsupported language: {language}")
    return strategy_class(generator)
