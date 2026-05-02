from src.generator.base import BaseGenerator
from src.utils.github import create_repo
from src.stack.profile import stack_registry, MonorepoSelection
from src.generator.layouts import monorepo_directories
from src.generator.specs import MonorepoSpec
from src.generator.template_plan import TemplatePlan
from src.utils.types import GeneratorConfig, TemplateValue

class MonorepoGenerator(BaseGenerator):
    helm: bool
    gh: bool
    cloud: str
    knowledge: str
    runtime: str
    spec: MonorepoSpec

    VALID_CLOUDS = set(stack_registry.clouds)
    VALID_KNOWLEDGE = set(stack_registry.knowledge)
    VALID_RUNTIMES = set(stack_registry.monorepo_runtimes)
    
    def __init__(
        self,
        name: str,
        gh: bool,
        config: GeneratorConfig,
        helm: bool = False,
        root: str | None = None,
        cloud: str = "multi",
        knowledge: str = "none",
        runtime: str = "kubernetes",
    ) -> None:
        spec = MonorepoSpec.from_options(
            name=name,
            gh=gh,
            config=config,
            helm=helm,
            root=root,
            cloud=cloud,
            knowledge=knowledge,
            runtime=runtime,
        )
        super().__init__(spec.name, spec.config, spec.root)
        self.spec = spec
        self.helm = spec.helm
        self.gh = spec.gh
        self.cloud = spec.cloud
        self.knowledge = spec.knowledge
        self.runtime = spec.runtime
        self.template_dir = self.template_dir / "monorepo"

    def create(self) -> None:
        selection = self._selection()

        directories = monorepo_directories(selection)
        
        template_vars = self._template_vars()
        template_plan = TemplatePlan.from_templates(selection.templates, template_vars)
        
        architecture_title: str = f"{self.name} Deployment Infra Docs"
        success_message: str = (
            f"Monorepo '{self.name}' scaffolded for {self._runtime_label()} "
            f"with {self._deployment_label()} support in '{self.project}'."
        )
        
        def github_create_fn() -> bool | None:
            return create_repo(self.name) if self.gh else None
        
        self.execute_create_flow(
            directories=directories,
            template_plan=template_plan,
            architecture_title=architecture_title,
            success_message=success_message,
            additional_setup_fn=self._setup_monorepo_specific,
            github_create_fn=github_create_fn if self.gh else None
        )
    
    def _setup_monorepo_specific(self) -> bool:
        """Setup monorepo-specific files and structure."""
        # Create and configure deployment infrastructure
        if self._uses_kubernetes():
            if self.helm:
                self._create_helm_structure()
            else:
                self._create_kustomize_structure()
        
        # Write documentation and configuration with variables
        self.write_template("Makefile", "Makefile.tpl", **self._template_vars())
        self.write_template("README.md", "README.md.tpl", **self._template_vars())
        return True

    def _validate_options(self) -> None:
        """Validate monorepo profile options."""
        self._selection()

    def _normalize_runtime(self, runtime: str) -> str:
        return stack_registry.normalize_monorepo_runtime(runtime)

    def _selection(self) -> MonorepoSelection:
        """Return the validated stack selection for this monorepo."""
        return stack_registry.monorepo_selection(self.cloud, self.knowledge, self.runtime, helm=self.helm)

    def _clouds(self) -> list[str]:
        """Return concrete cloud providers to scaffold."""
        return list(self._selection().clouds)

    def _include_backstage(self) -> bool:
        return self._selection().include_backstage

    def _include_obsidian(self) -> bool:
        return self._selection().include_obsidian

    def _uses_kubernetes(self) -> bool:
        return self._selection().uses_kubernetes

    def _uses_cloudflare_workers(self) -> bool:
        return self._selection().uses_cloudflare_workers

    def _runtime_label(self) -> str:
        return self._selection().runtime_label

    def _deployment_label(self) -> str:
        return self._selection().deployment_label

    def _template_vars(self) -> dict[str, TemplateValue]:
        selection = self._selection()
        return {
            "monorepo_name": self.name,
            "service_name": self.name,
            "cloud": selection.cloud,
            "clouds": list(selection.clouds),
            "cloud_label": selection.cloud_label,
            "runtime": selection.runtime,
            "runtime_label": selection.runtime_label,
            "include_aws": "aws" in selection.clouds,
            "include_gcp": "gcp" in selection.clouds,
            "include_cloudflare": "cloudflare" in selection.clouds,
            "uses_kubernetes": selection.uses_kubernetes,
            "uses_cloudflare_workers": selection.uses_cloudflare_workers,
            "knowledge": selection.knowledge,
            "include_backstage": selection.include_backstage,
            "include_obsidian": selection.include_obsidian,
            "deployment_tool": selection.deployment_label.lower(),
        }

    def _create_helm_structure(self) -> None:
        """Create Helm chart structure and files."""
        self.create_directories(["infra/helm/example-service/templates"])

        template_vars = self._template_vars()
        for template in stack_registry.helm_template_configs():
            self.write_template(template.target, template.template, **template_vars)

    def _create_kustomize_structure(self) -> None:
        """Create Kustomize structure and files."""
        self.create_directories([
            "infra/k8s/base",
            *[f"infra/k8s/overlays/{env}" for env in stack_registry.environments]
        ])

        template_vars = self._template_vars()
        for template in stack_registry.kustomize_template_configs():
            self.write_template(template.target, template.template, **template_vars)

        for env in stack_registry.environments:
            self.write_template(
                f"infra/k8s/overlays/{env}/kustomization.yaml",
                "kustomize/overlay-kustomization.yaml",
                **{**template_vars, "environment": env},
            )
