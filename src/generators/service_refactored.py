from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator
from src.generators.mixins import GitHubMixin, CommonTemplatesMixin
from src.generators.language_strategies import get_language_strategy
from src.utils.readme_generator import ReadmeGenerator
from src.utils.logger import success, warn


class ServiceGenerator(BaseGenerator, GitHubMixin, CommonTemplatesMixin):
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
        self.write_common_service_templates(self.lang)

        # Create language-specific structure using strategy pattern
        try:
            strategy = get_language_strategy(self.lang, self)
            strategy.create_structure()
        except ValueError as e:
            warn(str(e))
            return

        # Helm chart if requested
        if self.helm:
            self._create_helm_chart()

        self.log_success(f"{self.lang.title()} service '{self.name}' created successfully in '{self.project}'!")
        
        # Create GitHub repo if requested
        self.create_github_repo_if_requested()

    def _create_readme(self) -> None:
        """Create README.md using the ReadmeGenerator service."""
        readme_gen = ReadmeGenerator(self.name, self.lang)
        readme_content = readme_gen.generate_service_readme()
        
        # Write to a temporary shared template file and then use write_template
        temp_readme_path = self.template_dir / "_shared" / "readme_generated.tpl"
        temp_readme_path.write_text(readme_content)
        
        # Use write_template to handle variable substitution
        self.write_template("README.md", "_shared/readme_generated.tpl")
        
        # Clean up temporary file
        temp_readme_path.unlink()

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