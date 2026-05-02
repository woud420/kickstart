from src.generator.base import BaseGenerator
from src.generator.layouts import frontend_directories
from src.generator.specs import FrontendSpec
from src.utils.github import create_repo
from src.utils.types import GeneratorConfig

class FrontendGenerator(BaseGenerator):
    gh: bool
    spec: FrontendSpec
    
    def __init__(self, name: str, gh: bool, config: GeneratorConfig, root: str | None = None) -> None:
        spec = FrontendSpec(name=name, gh=gh, config=config, root=root)
        super().__init__(spec.name, spec.config, spec.root)
        self.spec = spec
        self.template_dir = self.template_dir / "react"
        self.gh = spec.gh

    def create(self) -> None:
        directories = frontend_directories()
        
        template_configs: list[dict[str, str]] = [
            {"target": "index.html", "template": "index.html.tpl"},
            {"target": ".gitignore", "template": "gitignore.tpl"},
            {"target": "Dockerfile", "template": "Dockerfile.tpl"},
            {"target": "Makefile", "template": "Makefile.tpl"},
            {"target": "README.md", "template": "README.md.tpl"},
            {"target": "package.json", "template": "package.json.tpl"},
            {"target": "tsconfig.json", "template": "tsconfig.json.tpl"},
            {"target": "vite.config.ts", "template": "vite.config.ts.tpl"},
            {"target": "src/App.tsx", "template": "src/App.tsx.tpl"},
            {"target": "src/main.tsx", "template": "src/main.tsx.tpl"},
            {"target": "tests/App.test.tsx", "template": "tests/App.test.tsx.tpl"},
        ]
        
        architecture_title: str = f"{self.name} Frontend Docs"
        success_message: str = f"Frontend app '{self.name}' created successfully in '{self.project}'!"
        
        def github_create_fn() -> bool | None:
            return create_repo(self.name) if self.gh else None

        self.execute_create_flow(
            directories=directories,
            template_configs=template_configs,
            architecture_title=architecture_title,
            success_message=success_message,
            github_create_fn=github_create_fn if self.gh else None
        )
