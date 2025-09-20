from typing import Any
from src.generator.base import BaseGenerator
from src.utils.github import create_repo

class FrontendGenerator(BaseGenerator):
    gh: bool
    
    def __init__(self, name: str, gh: bool, config: dict[str, Any], root: str | None = None) -> None:
        super().__init__(name, config, root)
        self.template_dir = self.template_dir / "react"
        self.gh = gh

    def create(self) -> None:
        directories: list[str] = ["src", "public", "tests", "architecture"]
        
        template_configs: list[dict[str, str]] = [
            {"target": ".gitignore", "template": "gitignore.tpl"},
            {"target": "Dockerfile", "template": "Dockerfile.tpl"},
            {"target": "Makefile", "template": "Makefile.tpl"},
            {"target": "README.md", "template": "README.md.tpl"},
            {"target": "package.json", "template": "package.json.tpl"}
        ]
        
        architecture_title: str = f"{self.name} Frontend Docs"
        success_message: str = f"Frontend app '{self.name}' created successfully in '{self.project}'!"
        
        def github_create_fn() -> Any:
            return create_repo(self.name) if self.gh else None

        self.execute_create_flow(
            directories=directories,
            template_configs=template_configs,
            architecture_title=architecture_title,
            success_message=success_message,
            github_create_fn=github_create_fn if self.gh else None
        )

