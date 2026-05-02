"""Declarative stack profile registry.

This module owns the compatibility matrix for Kickstart's preferred stack.
Generators should ask the registry what is valid instead of carrying their own
sets of string literals and runtime-specific template lists.
"""

from dataclasses import dataclass, field
from typing import Mapping

from src.utils.types import TemplateConfigDict, TemplateVars
from src.utils.error_handling import LanguageNotSupportedError


@dataclass(frozen=True)
class TemplateConfig:
    """Template target and source path with optional context-specific vars."""

    target: str
    template: str
    vars: TemplateVars = field(default_factory=dict)

    def as_dict(self, base_vars: TemplateVars | None = None) -> TemplateConfigDict:
        """Return a generator-compatible template config."""
        config: TemplateConfigDict = {"target": self.target, "template": self.template}
        merged_vars = dict(base_vars or {})
        merged_vars.update(self.vars)
        if merged_vars:
            config["vars"] = merged_vars
        return config

    def as_plain_dict(self) -> dict[str, str]:
        """Return a simple target/template mapping for service generators."""
        return {"target": self.target, "template": self.template}


@dataclass(frozen=True)
class LanguageProfile:
    """Language support metadata."""

    id: str
    display_name: str
    aliases: tuple[str, ...] = ()
    service_runtimes: tuple[str, ...] = ("container",)
    library: bool = False
    cli: bool = False
    smoke_commands: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeProfile:
    """Runtime target metadata."""

    id: str
    display_name: str
    aliases: tuple[str, ...] = ()
    service_languages: tuple[str, ...] = ()
    deployment_tools: tuple[str, ...] = ()
    smoke_commands: tuple[str, ...] = ()
    uses_kubernetes: bool = False
    uses_cloudflare_workers: bool = False


@dataclass(frozen=True)
class CloudProfile:
    """Cloud provider selection metadata."""

    id: str
    display_name: str
    providers: tuple[str, ...]
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeProfile:
    """Knowledge-base scaffold metadata."""

    id: str
    display_name: str
    include_obsidian: bool
    include_backstage: bool
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeploymentToolProfile:
    """Deployment tool metadata."""

    id: str
    display_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ServiceSelection:
    """Validated service scaffold selection."""

    language: str
    runtime: str
    deployment_tool: str
    templates: tuple[TemplateConfig, ...]
    smoke_commands: tuple[str, ...]

    def template_configs(self) -> list[dict[str, str]]:
        """Return generator-compatible template configs."""
        return [template.as_plain_dict() for template in self.templates]


@dataclass(frozen=True)
class MonorepoSelection:
    """Validated monorepo scaffold selection."""

    cloud: str
    clouds: tuple[str, ...]
    knowledge: str
    runtime: str
    deployment_tool: str
    deployment_label: str
    runtime_label: str
    include_obsidian: bool
    include_backstage: bool
    uses_kubernetes: bool
    uses_cloudflare_workers: bool
    templates: tuple[TemplateConfig, ...]
    smoke_commands: tuple[str, ...]

    @property
    def cloud_label(self) -> str:
        """Human-readable cloud provider label."""
        return ", ".join(self.clouds).upper() if self.clouds else "local-only"

    def template_configs(self, base_vars: TemplateVars) -> list[TemplateConfigDict]:
        """Return generator-compatible template configs."""
        return [template.as_dict(base_vars) for template in self.templates]


class StackProfileRegistry:
    """Source of truth for stack support, aliases, and compatibility."""

    environments = ("dev", "staging", "prod")

    def __init__(self) -> None:
        self.languages = {
            "python": LanguageProfile(
                id="python",
                display_name="Python",
                service_runtimes=("container",),
                library=True,
                cli=True,
                smoke_commands={
                    "container": ("make install", "make test", "make typecheck"),
                },
            ),
            "rust": LanguageProfile(
                id="rust",
                display_name="Rust",
                service_runtimes=("container", "cloudflare-workers"),
                library=True,
                cli=True,
                smoke_commands={
                    "container": ("make test", "make build"),
                    "cloudflare-workers": ("make install", "make check", "make build"),
                },
            ),
            "typescript": LanguageProfile(
                id="typescript",
                display_name="TypeScript",
                aliases=("ts",),
                service_runtimes=("container", "cloudflare-workers"),
                smoke_commands={
                    "container": ("make install", "make typecheck", "make test", "make build"),
                    "cloudflare-workers": ("make install", "make typecheck", "make test"),
                },
            ),
            "cpp": LanguageProfile(
                id="cpp",
                display_name="C++",
                aliases=("c++", "cxx"),
                service_runtimes=("container",),
                smoke_commands={
                    "container": ("make build", "make test"),
                },
            ),
            "go": LanguageProfile(
                id="go",
                display_name="Go",
                service_runtimes=("container",),
                library=True,
                cli=True,
                smoke_commands={
                    "container": ("make test", "make build"),
                },
            ),
        }

        self.service_runtimes = {
            "container": RuntimeProfile(
                id="container",
                display_name="Container",
                aliases=("docker", "containers"),
                service_languages=("python", "rust", "typescript", "cpp", "go"),
                deployment_tools=("docker", "helm"),
            ),
            "cloudflare-workers": RuntimeProfile(
                id="cloudflare-workers",
                display_name="Cloudflare Workers",
                aliases=("cloudflare-worker", "cf-worker", "cf-workers", "worker", "workers"),
                service_languages=("typescript", "rust"),
                deployment_tools=("wrangler",),
                uses_cloudflare_workers=True,
            ),
        }

        self.monorepo_runtimes = {
            "kubernetes": RuntimeProfile(
                id="kubernetes",
                display_name="Kubernetes",
                aliases=("k8s",),
                deployment_tools=("kustomize", "helm"),
                smoke_commands=("make install", "make test", "make k8s-render ENV=dev", "make tf-plan ENV=dev"),
                uses_kubernetes=True,
            ),
            "cloudflare-workers": RuntimeProfile(
                id="cloudflare-workers",
                display_name="Cloudflare Workers",
                aliases=("cloudflare-worker", "cf-worker", "cf-workers", "worker", "workers"),
                deployment_tools=("wrangler",),
                smoke_commands=("make install", "make test", "make cf-worker-notes", "make tf-plan ENV=dev"),
                uses_cloudflare_workers=True,
            ),
            "hybrid": RuntimeProfile(
                id="hybrid",
                display_name="Kubernetes and Cloudflare Workers",
                deployment_tools=("kustomize", "helm", "wrangler"),
                smoke_commands=(
                    "make install",
                    "make test",
                    "make k8s-render ENV=dev",
                    "make cf-worker-notes",
                    "make tf-plan ENV=dev",
                ),
                uses_kubernetes=True,
                uses_cloudflare_workers=True,
            ),
        }

        self.clouds = {
            "aws": CloudProfile(id="aws", display_name="AWS", providers=("aws",)),
            "gcp": CloudProfile(id="gcp", display_name="GCP", providers=("gcp",), aliases=("google",)),
            "cloudflare": CloudProfile(
                id="cloudflare",
                display_name="Cloudflare",
                providers=("cloudflare",),
                aliases=("cf",),
            ),
            "multi": CloudProfile(
                id="multi",
                display_name="Multi-cloud",
                providers=("aws", "gcp", "cloudflare"),
                aliases=("all",),
            ),
            "none": CloudProfile(id="none", display_name="Local only", providers=(), aliases=("local", "local-only")),
        }

        self.knowledge = {
            "none": KnowledgeProfile(id="none", display_name="None", include_obsidian=False, include_backstage=False),
            "obsidian": KnowledgeProfile(
                id="obsidian",
                display_name="Obsidian",
                include_obsidian=True,
                include_backstage=False,
            ),
            "backstage": KnowledgeProfile(
                id="backstage",
                display_name="Backstage",
                include_obsidian=False,
                include_backstage=True,
            ),
            "both": KnowledgeProfile(
                id="both",
                display_name="Backstage and Obsidian",
                include_obsidian=True,
                include_backstage=True,
            ),
        }

        self.deployment_tools = {
            "docker": DeploymentToolProfile(id="docker", display_name="Docker"),
            "kustomize": DeploymentToolProfile(id="kustomize", display_name="Kustomize"),
            "helm": DeploymentToolProfile(id="helm", display_name="Helm"),
            "wrangler": DeploymentToolProfile(id="wrangler", display_name="Wrangler"),
        }

    def normalize_language(self, language: str) -> str:
        """Normalize language aliases, preserving unknown values for later validation."""
        return self._normalize(language, self.languages)

    def normalize_service_runtime(self, runtime: str) -> str:
        """Normalize service runtime aliases, preserving unknown values for validation."""
        return self._normalize(runtime, self.service_runtimes)

    def normalize_monorepo_runtime(self, runtime: str) -> str:
        """Normalize monorepo runtime aliases, preserving unknown values for validation."""
        return self._normalize(runtime, self.monorepo_runtimes)

    def normalize_cloud(self, cloud: str) -> str:
        """Normalize cloud aliases, preserving unknown values for validation."""
        return self._normalize(cloud, self.clouds)

    def normalize_knowledge(self, knowledge: str) -> str:
        """Normalize knowledge aliases, preserving unknown values for validation."""
        return self._normalize(knowledge, self.knowledge)

    def service_selection(self, language: str, runtime: str = "container", *, helm: bool = False) -> ServiceSelection:
        """Validate and describe a service scaffold selection."""
        normalized_language = self.normalize_language(language)
        normalized_runtime = self.normalize_service_runtime(runtime)

        language_profile = self.languages.get(normalized_language)
        if language_profile is None:
            raise LanguageNotSupportedError(
                "Language '{language}' is not supported. Supported languages: {supported}".format(
                    language=language,
                    supported=", ".join(sorted(self.languages)),
                )
            )

        runtime_profile = self.service_runtimes.get(normalized_runtime)
        if runtime_profile is None:
            raise ValueError(
                "Unsupported service runtime: {runtime}. Use one of: {supported}.".format(
                    runtime=runtime,
                    supported=", ".join(sorted(self.service_runtimes)),
                )
            )

        if normalized_runtime not in language_profile.service_runtimes:
            raise LanguageNotSupportedError(
                "Language '{language}' does not support service runtime '{runtime}'. Supported runtimes: {supported}".format(
                    language=normalized_language,
                    runtime=normalized_runtime,
                    supported=", ".join(language_profile.service_runtimes),
                )
            )

        if helm and normalized_runtime == "cloudflare-workers":
            raise ValueError("Cloudflare Workers runtime does not support Helm service charts.")

        deployment_tool = "helm" if helm and normalized_runtime == "container" else runtime_profile.deployment_tools[0]
        return ServiceSelection(
            language=normalized_language,
            runtime=normalized_runtime,
            deployment_tool=deployment_tool,
            templates=self._service_templates(normalized_language, normalized_runtime),
            smoke_commands=language_profile.smoke_commands.get(normalized_runtime, ()),
        )

    def service_template_configs(self, language: str, runtime: str = "container") -> list[dict[str, str]]:
        """Return template mappings for a service selection."""
        return self.service_selection(language, runtime).template_configs()

    def monorepo_selection(
        self,
        cloud: str = "multi",
        knowledge: str = "both",
        runtime: str = "kubernetes",
        *,
        helm: bool = False,
    ) -> MonorepoSelection:
        """Validate and describe a monorepo scaffold selection."""
        normalized_cloud = self.normalize_cloud(cloud)
        normalized_knowledge = self.normalize_knowledge(knowledge)
        normalized_runtime = self.normalize_monorepo_runtime(runtime)

        cloud_profile = self.clouds.get(normalized_cloud)
        if cloud_profile is None:
            raise ValueError(
                "Unsupported cloud target '{cloud}'. Use one of: {supported}".format(
                    cloud=cloud,
                    supported=", ".join(sorted(self.clouds)),
                )
            )

        knowledge_profile = self.knowledge.get(normalized_knowledge)
        if knowledge_profile is None:
            raise ValueError(
                "Unsupported knowledge scaffold '{knowledge}'. Use one of: {supported}".format(
                    knowledge=knowledge,
                    supported=", ".join(sorted(self.knowledge)),
                )
            )

        runtime_profile = self.monorepo_runtimes.get(normalized_runtime)
        if runtime_profile is None:
            raise ValueError(
                "Unsupported runtime target '{runtime}'. Use one of: {supported}".format(
                    runtime=runtime,
                    supported=", ".join(sorted(self.monorepo_runtimes)),
                )
            )

        deployment_tool, deployment_label = self._monorepo_deployment(runtime_profile, helm=helm)
        return MonorepoSelection(
            cloud=normalized_cloud,
            clouds=cloud_profile.providers,
            knowledge=normalized_knowledge,
            runtime=normalized_runtime,
            deployment_tool=deployment_tool,
            deployment_label=deployment_label,
            runtime_label=runtime_profile.display_name,
            include_obsidian=knowledge_profile.include_obsidian,
            include_backstage=knowledge_profile.include_backstage,
            uses_kubernetes=runtime_profile.uses_kubernetes,
            uses_cloudflare_workers=runtime_profile.uses_cloudflare_workers,
            templates=self._monorepo_templates(knowledge_profile, runtime_profile),
            smoke_commands=runtime_profile.smoke_commands,
        )

    def kustomize_template_configs(self) -> tuple[TemplateConfig, ...]:
        """Return Kubernetes Kustomize template mappings."""
        return (
            TemplateConfig("infra/k8s/base/kustomization.yaml", "kustomize/kustomization.yaml"),
            TemplateConfig("infra/k8s/base/deployment.yaml", "kustomize/deployment.yaml"),
            TemplateConfig("infra/k8s/base/service.yaml", "kustomize/service.yaml"),
            TemplateConfig("infra/k8s/base/configmap.yaml", "kustomize/configmap.yaml"),
            TemplateConfig("infra/k8s/base/secret.yaml", "kustomize/secret.yaml"),
            TemplateConfig("infra/k8s/base/hpa.yaml", "kustomize/hpa.yaml"),
            TemplateConfig("infra/k8s/base/networkpolicy.yaml", "kustomize/networkpolicy.yaml"),
        )

    def helm_template_configs(self) -> tuple[TemplateConfig, ...]:
        """Return Helm chart template mappings."""
        return (
            TemplateConfig("infra/helm/example-service/Chart.yaml", "helm/Chart.yaml"),
            TemplateConfig("infra/helm/example-service/values.yaml", "helm/values.yaml"),
            TemplateConfig("infra/helm/example-service/templates/deployment.yaml", "helm/deployment.yaml"),
            TemplateConfig("infra/helm/example-service/templates/service.yaml", "helm/service.yaml"),
            TemplateConfig("infra/helm/example-service/templates/configmap.yaml", "helm/configmap.yaml"),
            TemplateConfig("infra/helm/example-service/templates/_helpers.tpl", "helm/_helpers.tpl"),
        )

    def _service_templates(self, language: str, runtime: str) -> tuple[TemplateConfig, ...]:
        if runtime == "cloudflare-workers":
            return self._cloudflare_worker_service_templates(language)

        common = (
            TemplateConfig("README.md", f"{language}/README.md.tpl"),
            TemplateConfig(".gitignore", f"{language}/gitignore.tpl"),
            TemplateConfig("Dockerfile", f"{language}/Dockerfile.tpl"),
            TemplateConfig("Makefile", f"{language}/Makefile.tpl"),
        )
        language_specific = {
            "python": (
                TemplateConfig("requirements.txt", "python/requirements.txt.tpl"),
                TemplateConfig("pyproject.toml", "python/pyproject.toml.tpl"),
            ),
            "rust": (TemplateConfig("Cargo.toml", "rust/Cargo.toml.tpl"),),
            "go": (TemplateConfig("go.mod", "go/go.mod.tpl"),),
            "typescript": (
                TemplateConfig("package.json", "typescript/package.json.tpl"),
                TemplateConfig("tsconfig.json", "typescript/tsconfig.json.tpl"),
                TemplateConfig("tsconfig.build.json", "typescript/tsconfig.build.json.tpl"),
                TemplateConfig("bunfig.toml", "typescript/bunfig.toml.tpl"),
            ),
            "cpp": (TemplateConfig("CMakeLists.txt", "cpp/CMakeLists.txt.tpl"),),
        }
        return common + language_specific.get(language, ())

    def _cloudflare_worker_service_templates(self, language: str) -> tuple[TemplateConfig, ...]:
        base = f"cloudflare-workers/{language}"
        common = (
            TemplateConfig("README.md", f"{base}/README.md.tpl"),
            TemplateConfig(".gitignore", f"{base}/gitignore.tpl"),
            TemplateConfig("Makefile", f"{base}/Makefile.tpl"),
            TemplateConfig("wrangler.toml", f"{base}/wrangler.toml.tpl"),
            TemplateConfig(".dev.vars.example", f"{base}/dev.vars.example.tpl"),
        )
        worker_specific = {
            "typescript": (
                TemplateConfig("package.json", f"{base}/package.json.tpl"),
                TemplateConfig("tsconfig.json", f"{base}/tsconfig.json.tpl"),
                TemplateConfig("src/index.ts", f"{base}/src/index.ts.tpl"),
                TemplateConfig("tests/worker.test.ts", f"{base}/tests/worker.test.ts.tpl"),
            ),
            "rust": (
                TemplateConfig("Cargo.toml", f"{base}/Cargo.toml.tpl"),
                TemplateConfig("package.json", f"{base}/package.json.tpl"),
                TemplateConfig("src/lib.rs", f"{base}/src/lib.rs.tpl"),
                TemplateConfig("tests/README.md", f"{base}/tests/README.md.tpl"),
            ),
        }
        return common + worker_specific[language]

    def _monorepo_templates(
        self,
        knowledge_profile: KnowledgeProfile,
        runtime_profile: RuntimeProfile,
    ) -> tuple[TemplateConfig, ...]:
        templates = [
            TemplateConfig("infra/docker/docker-compose.yml", "docker-compose.yml"),
            TemplateConfig("infra/terraform/versions.tf", "terraform_versions.tf"),
            TemplateConfig("infra/terraform/providers.tf", "terraform_providers.tf"),
            TemplateConfig("infra/terraform/modules/service_runtime/main.tf", "terraform_module_service_runtime.tf"),
            TemplateConfig("data/postgres/schema.sql", "postgres_schema.sql"),
            TemplateConfig("docs/adr/0001-stack-profile.md", "adr_stack_profile.md"),
            TemplateConfig("docs/agents/recommended-agents.md", "agents_recommended.md"),
            TemplateConfig("docs/architecture/context.md", "architecture_context.md"),
            TemplateConfig("docs/data/README.md", "data_readme.md"),
            TemplateConfig("docs/knowledge/README.md", "knowledge_readme.md"),
            TemplateConfig("knowledge/README.md", "knowledge_root_readme.md"),
            TemplateConfig("package.json", "package.json.tpl"),
            TemplateConfig("turbo.json", "turbo.json.tpl"),
            TemplateConfig("bunfig.toml", "bunfig.toml.tpl"),
            TemplateConfig("config/tsconfig/base.json", "tsconfig_base.json.tpl"),
        ]

        for env in self.environments:
            templates.extend(
                [
                    TemplateConfig(f"infra/terraform/env/{env}/main.tf", "terraform_env_main.tf", {"environment": env}),
                    TemplateConfig(
                        f"infra/terraform/env/{env}/variables.tf",
                        "variables.tf",
                        {"environment": env},
                    ),
                    TemplateConfig(
                        f"infra/terraform/env/{env}/terraform.tfvars.example",
                        "terraform.tfvars.example",
                        {"environment": env},
                    ),
                ]
            )

        templates.extend(
            [
                TemplateConfig(".github/workflows/build.yml", "build.yml"),
                TemplateConfig(".github/workflows/test.yml", "test.yml"),
                TemplateConfig(".github/workflows/deploy.yml", "deploy.yml"),
            ]
        )

        if knowledge_profile.include_backstage:
            templates.extend(
                [
                    TemplateConfig("catalog-info.yaml", "catalog-info.yaml"),
                    TemplateConfig("templates/backstage/template.yaml", "backstage_template.yaml"),
                ]
            )

        if knowledge_profile.include_obsidian:
            templates.extend(
                [
                    TemplateConfig(".obsidian/app.json", "obsidian_app.json"),
                    TemplateConfig(".obsidian/graph.json", "obsidian_graph.json"),
                ]
            )

        if runtime_profile.uses_cloudflare_workers:
            templates.extend(
                [
                    TemplateConfig("infra/cloudflare/workers/README.md", "cloudflare_workers_readme.md"),
                    TemplateConfig("infra/cloudflare/workers/wrangler.example.toml", "cloudflare_workers_wrangler.toml"),
                ]
            )

        return tuple(templates)

    def _monorepo_deployment(self, runtime_profile: RuntimeProfile, *, helm: bool) -> tuple[str, str]:
        if runtime_profile.uses_kubernetes and runtime_profile.uses_cloudflare_workers:
            return ("helm+wrangler", "Helm and Wrangler") if helm else ("kustomize+wrangler", "Kustomize and Wrangler")
        if runtime_profile.uses_kubernetes:
            return ("helm", "Helm") if helm else ("kustomize", "Kustomize")
        return "wrangler", "Wrangler"

    def _normalize(
        self,
        value: str,
        profiles: Mapping[str, LanguageProfile | RuntimeProfile | CloudProfile | KnowledgeProfile],
    ) -> str:
        candidate = value.strip().lower()
        if candidate in profiles:
            return candidate
        for profile in profiles.values():
            aliases = getattr(profile, "aliases", ())
            if candidate in aliases:
                return str(profile.id)
        return candidate


stack_registry = StackProfileRegistry()
