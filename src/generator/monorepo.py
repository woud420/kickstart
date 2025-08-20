from pathlib import Path
from typing import Any
from src.generator.base import BaseGenerator
from src.utils.github import create_repo

class MonorepoGenerator(BaseGenerator):
    helm: bool
    gh: bool
    
    def __init__(self, name: str, gh: bool, config: dict[str, Any], helm: bool = False, root: str | None = None) -> None:
        super().__init__(name, config, root)
        self.helm = helm
        self.gh = gh
        self.template_dir = self.template_dir / "monorepo"

    def create(self) -> None:
        directories: list[str] = [
            "infra/docker",
            "infra/terraform/modules/example_module",
            *[f"infra/terraform/env/{env}" for env in ["dev", "staging", "prod"]],
            ".github/workflows",
            "architecture"
        ]
        
        template_configs: list[dict[str, str]] = [
            {"target": "infra/docker/docker-compose.yml", "template": "docker-compose.yml"}
        ]
        
        # Add Terraform files for each environment
        for env in ["dev", "staging", "prod"]:
            template_configs.extend([
                {"target": f"infra/terraform/env/{env}/main.tf", "template": "terraform_env_main.tf"},
                {"target": f"infra/terraform/env/{env}/variables.tf", "template": "variables.tf"}
            ])
        
        # Add GitHub workflow files
        for wf in ["build.yml", "test.yml", "deploy.yml"]:
            template_configs.append({"target": f".github/workflows/{wf}", "template": wf})
        
        architecture_title: str = f"{self.name} Deployment Infra Docs"
        success_message: str = f"Monorepo '{self.name}' scaffolded with {'Helm' if self.helm else 'Kustomize'} support in '{self.project}'."
        
        github_create_fn = lambda: create_repo(self.name) if self.gh else None
        
        self.execute_create_flow(
            directories=directories,
            template_configs=template_configs,
            architecture_title=architecture_title,
            success_message=success_message,
            additional_setup_fn=self._setup_monorepo_specific,
            github_create_fn=github_create_fn if self.gh else None
        )
    
    def _setup_monorepo_specific(self) -> None:
        """Setup monorepo-specific files and structure."""
        # Create and configure deployment infrastructure
        if self.helm:
            self._create_helm_structure()
        else:
            self._create_kustomize_structure()
        
        # Write documentation and configuration with variables
        self.write_template("Makefile", "Makefile.tpl", monorepo_name=self.name)
        self.write_template("README.md", "README.md.tpl", monorepo_name=self.name)

    def _create_helm_structure(self) -> None:
        """Create Helm chart structure and files."""
        self.create_directories(["infra/helm/example-service/templates"])
        
        self.write_template("infra/helm/example-service/Chart.yaml", "helm/Chart.yaml")
        self.write_template("infra/helm/example-service/values.yaml", "helm/values.yaml")
        self.write_template("infra/helm/example-service/templates/deployment.yaml", "helm/deployment.yaml")

    def _create_kustomize_structure(self) -> None:
        """Create Kustomize structure and files."""
        self.create_directories([
            "infra/k8s/base",
            *[f"infra/k8s/overlays/{env}" for env in ["dev", "staging", "prod"]]
        ])

        self.write_template("infra/k8s/base/kustomization.yaml", "kustomize/kustomization.yaml")
        self.write_template("infra/k8s/base/deployment.yaml", "kustomize/deployment.yaml")
        self.write_template("infra/k8s/base/service.yaml", "kustomize/service.yaml")

