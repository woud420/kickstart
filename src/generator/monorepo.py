from src.generator.base import BaseGenerator
from src.utils.github import create_repo
from src.stack.profile import stack_registry, SystemSelection
from src.generator.layouts import system_directories
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract
from src.generator.specs import SystemSpec
from src.generator.template_plan import TemplatePlan
from src.utils.types import GeneratorConfig, TemplateValue


class SystemGenerator(BaseGenerator):
    helm: bool
    gh: bool
    cloud: str
    knowledge: str
    runtime: str
    workspace_tooling: str
    spec: SystemSpec
    selection: SystemSelection

    VALID_CLOUDS = set(stack_registry.clouds)
    VALID_KNOWLEDGE = set(stack_registry.knowledge)
    VALID_RUNTIMES = set(stack_registry.system_runtimes)
    
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
        workspace_tooling: str = "none",
    ) -> None:
        spec = SystemSpec.from_options(
            name=name,
            gh=gh,
            config=config,
            helm=helm,
            root=root,
            cloud=cloud,
            knowledge=knowledge,
            runtime=runtime,
            workspace_tooling=workspace_tooling,
        )
        super().__init__(spec.name, spec.config, spec.root)
        self.spec = spec
        self.helm = spec.helm
        self.gh = spec.gh
        self.cloud = spec.cloud
        self.knowledge = spec.knowledge
        self.runtime = spec.runtime
        self.workspace_tooling = spec.workspace_tooling
        self.selection = stack_registry.system_selection(
            self.cloud,
            self.knowledge,
            self.runtime,
            self.workspace_tooling,
            helm=self.helm,
        )
        self.template_dir = self.template_dir / "monorepo"

    def create(self) -> None:
        selection = self.selection

        directories = system_directories(selection)
        
        template_vars = self._template_vars()
        template_plan = TemplatePlan.from_templates(selection.templates, template_vars)
        
        architecture_title: str = f"{self.name} System Docs"
        success_message: str = (
            f"System '{self.name}' scaffolded as a monorepo for {self._runtime_label()} "
            f"with {self._artifact_label()} artifacts in '{self.project}'."
        )
        
        def github_create_fn() -> bool | None:
            return create_repo(self.name) if self.gh else None
        
        self.execute_create_flow(
            directories=directories,
            template_plan=template_plan,
            architecture_title=architecture_title,
            scaffold_contract=ScaffoldContract(
                project_kind="system",
                repo_layout="monorepo",
                execution_models=self._execution_models(selection),
                runtime_platforms=self._runtime_platforms(selection),
                artifacts=self._artifact_contract(selection),
                provider_targets=selection.clouds,
                knowledge_adapter=selection.knowledge,
                workspace_tooling=selection.workspace_tooling,
            ),
            success_message=success_message,
            additional_setup_fn=self._setup_system_specific,
            github_create_fn=github_create_fn if self.gh else None
        )
    
    def _setup_system_specific(self) -> bool:
        """Setup system-specific files and structure."""
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
        """Validate system profile options."""
        self._selection()

    def _normalize_runtime(self, runtime: str) -> str:
        return stack_registry.normalize_system_runtime(runtime)

    def _selection(self) -> SystemSelection:
        """Return the validated stack selection for this system."""
        return self.selection

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

    def _artifact_label(self) -> str:
        return self._selection().artifact_label

    def _execution_models(self, selection: SystemSelection) -> tuple[str, ...]:
        """Return execution models represented by this system scaffold."""
        models: list[str] = []
        if selection.uses_kubernetes:
            models.append("container")
        if selection.uses_cloudflare_workers:
            models.append("cloudflare-worker")
        return tuple(models)

    def _runtime_platforms(self, selection: SystemSelection) -> tuple[str, ...]:
        """Return runtime platforms represented by this system scaffold."""
        platforms: list[str] = []
        if selection.uses_kubernetes:
            platforms.append("kubernetes")
        if selection.uses_cloudflare_workers:
            platforms.append("cloudflare-workers")
        return tuple(platforms)

    def _artifact_contract(self, selection: SystemSelection) -> ScaffoldArtifacts:
        """Return emitted artifact categories for the system scaffold."""
        kubernetes_artifact = None
        if selection.uses_kubernetes:
            kubernetes_artifact = selection.artifact_tool.removesuffix("+wrangler")
        return ScaffoldArtifacts(
            local="compose",
            iac="terraform",
            ci="github-actions",
            kubernetes=kubernetes_artifact,
            worker="wrangler" if selection.uses_cloudflare_workers else None,
        )

    def _template_vars(self) -> dict[str, TemplateValue]:
        selection = self.selection
        return {
            "system_name": self.name,
            "monorepo_name": self.name,
            "service_name": self.name,
            "cloud": selection.cloud,
            "clouds": list(selection.clouds),
            "provider_targets": list(selection.clouds),
            "cloud_label": selection.cloud_label,
            "runtime": selection.runtime,
            "runtime_label": selection.runtime_label,
            "workspace_tooling": selection.workspace_tooling,
            "workspace_tooling_label": selection.workspace_tooling_label,
            "uses_bun_turbo": selection.uses_bun_turbo,
            "include_aws": "aws" in selection.clouds,
            "include_gcp": "gcp" in selection.clouds,
            "include_cloudflare": "cloudflare" in selection.clouds,
            "uses_kubernetes": selection.uses_kubernetes,
            "uses_cloudflare_workers": selection.uses_cloudflare_workers,
            "knowledge": selection.knowledge,
            "include_backstage": selection.include_backstage,
            "include_obsidian": selection.include_obsidian,
            "artifact_label": selection.artifact_label.lower(),
        }

    def _create_helm_structure(self) -> None:
        """Create Helm chart structure and files."""
        self.create_directories(["infra/helm/example-service/templates"])

        template_vars = self._template_vars()
        self.write_template_configs(stack_registry.helm_template_configs(), template_vars)

    def _create_kustomize_structure(self) -> None:
        """Create Kustomize structure and files."""
        self.create_directories([
            "infra/k8s/base",
            *[f"infra/k8s/overlays/{env}" for env in stack_registry.environments]
        ])

        template_vars = self._template_vars()
        self.write_template_configs(stack_registry.kustomize_template_configs(), template_vars)

        for env in stack_registry.environments:
            self.write_template(
                f"infra/k8s/overlays/{env}/kustomization.yaml",
                "kustomize/overlay-kustomization.yaml",
                **{**template_vars, "environment": env},
            )
class MonorepoGenerator(SystemGenerator):
    """Legacy monorepo generator.

    The legacy monorepo entry point keeps the historical Bun + Turbo workspace
    default. The canonical system entry point is neutral by default.
    """

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
        workspace_tooling: str = "bun-turbo",
    ) -> None:
        super().__init__(
            name,
            gh,
            config,
            helm=helm,
            root=root,
            cloud=cloud,
            knowledge=knowledge,
            runtime=runtime,
            workspace_tooling=workspace_tooling,
        )
