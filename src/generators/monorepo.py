from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator
from src.utils.github import create_repo

class MonorepoGenerator(BaseGenerator):
    def __init__(self, name: str, gh: bool, config: dict, helm: bool = False, root: Optional[str] = None):
        super().__init__(name, config, root)
        self.helm = helm
        self.gh = gh
        self.template_dir = self.template_dir / "monorepo"

    def create(self) -> None:
        if not self.create_project():
            return

        # Create infrastructure directories
        self.create_directories([
            "infra/docker",
            "infra/terraform/modules/example_module",
            *[f"infra/terraform/env/{env}" for env in ["dev", "staging", "prod"]],
            ".github/workflows",
            "architecture"
        ])

        # Create and configure deployment infrastructure
        if self.helm:
            self._create_helm_structure()
        else:
            self._create_kustomize_structure()

        # Write Docker and Terraform files
        self.write_template("infra/docker/docker-compose.yml", "docker-compose.yml")
        
        # Write Terraform files for each environment
        for env in ["dev", "staging", "prod"]:
            self.write_template(f"infra/terraform/env/{env}/main.tf", "terraform_env_main.tf")
            self.write_template(f"infra/terraform/env/{env}/variables.tf", "variables.tf")

        # Write GitHub workflow files
        for wf in ["build.yml", "test.yml", "deploy.yml"]:
            self.write_template(f".github/workflows/{wf}", wf)

        # Write documentation and configuration
        self.write_content("architecture/README.md", f"# {self.name} Deployment Infra Docs\n")
        self.write_template("Makefile", "Makefile.tpl", monorepo_name=self.name)
        self.write_template("README.md", "README.md.tpl", monorepo_name=self.name)

        self.log_success(f"Monorepo '{self.name}' scaffolded with {'Helm' if self.helm else 'Kustomize'} support in '{self.project}'.")

        if self.gh:
            create_repo(self.name)

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

def create_monorepo(name: str, gh: bool, config: dict, helm: bool = False, root: str = None):
    """Factory function for backward compatibility"""
    generator = MonorepoGenerator(name, gh, config, helm, root)
    generator.create()

