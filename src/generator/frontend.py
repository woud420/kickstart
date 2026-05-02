from src.generator.base import BaseGenerator
from src.generator.layouts import frontend_directories
from src.generator.scaffold_contract import ScaffoldContract
from src.generator.specs import FrontendSpec
from src.generator.template_plans import frontend_template_plan
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
        template_plan = frontend_template_plan()
        
        architecture_title: str = f"{self.name} Frontend Docs"
        success_message: str = f"Frontend app '{self.name}' created successfully in '{self.project}'!"
        
        def github_create_fn() -> bool | None:
            return create_repo(self.name) if self.gh else None

        self.execute_create_flow(
            directories=directories,
            template_plan=template_plan,
            architecture_title=architecture_title,
            scaffold_contract=ScaffoldContract(
                project_kind="frontend",
                runtime="static-spa",
                deploy="docker",
            ),
            success_message=success_message,
            github_create_fn=github_create_fn if self.gh else None
        )
