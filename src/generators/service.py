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
            "tests/unit",
            "tests/integration",
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

        # Language-specific files
        if self.lang == "python":
            self.write_template("requirements.txt", "python/requirements.txt.tpl")
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.toml.tpl")

        # Helm chart if requested
        if self.helm:
            self._create_helm_chart()

        self.log_success(f"{self.lang.title()} service '{self.name}' created successfully in '{self.project}'!")

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

