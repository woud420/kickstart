"""Stack profile registry selection logic."""

from typing import Mapping

from src.stack import defaults
from src.stack import templates
from src.stack.types import (
    MonorepoSelection,
    Profile,
    RuntimeProfile,
    ServiceSelection,
    TemplateConfig,
)
from src.utils.error_handling import LanguageNotSupportedError


class StackProfileRegistry:
    """Source of truth for stack support, aliases, and compatibility."""

    def __init__(self) -> None:
        self.environments = defaults.environments
        self.languages = dict(defaults.languages)
        self.service_runtimes = dict(defaults.service_runtimes)
        self.monorepo_runtimes = dict(defaults.monorepo_runtimes)
        self.clouds = dict(defaults.clouds)
        self.knowledge = dict(defaults.knowledge)
        self.artifact_tools = dict(defaults.artifact_tools)

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

        artifact_tool = "helm" if helm and normalized_runtime == "container" else runtime_profile.artifact_tools[0]
        return ServiceSelection(
            language=normalized_language,
            runtime=normalized_runtime,
            artifact_tool=artifact_tool,
            templates=templates.service_templates(normalized_language, normalized_runtime),
            smoke_commands=language_profile.smoke_commands.get(normalized_runtime, ()),
        )

    def service_template_configs(self, language: str, runtime: str = "container") -> list[dict[str, str]]:
        """Return template mappings for a service selection."""
        return self.service_selection(language, runtime).template_configs()

    def monorepo_selection(
        self,
        cloud: str = "multi",
        knowledge: str = "none",
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
                "Unsupported provider target '{cloud}'. Use one of: {supported}".format(
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
                "Unsupported monorepo platform profile '{runtime}'. Use one of: {supported}".format(
                    runtime=runtime,
                    supported=", ".join(sorted(self.monorepo_runtimes)),
                )
            )

        artifact_tool, artifact_label = self._monorepo_artifacts(runtime_profile, helm=helm)
        return MonorepoSelection(
            cloud=normalized_cloud,
            clouds=cloud_profile.providers,
            knowledge=normalized_knowledge,
            runtime=normalized_runtime,
            artifact_tool=artifact_tool,
            artifact_label=artifact_label,
            runtime_label=runtime_profile.display_name,
            include_obsidian=knowledge_profile.include_obsidian,
            include_backstage=knowledge_profile.include_backstage,
            uses_kubernetes=runtime_profile.uses_kubernetes,
            uses_cloudflare_workers=runtime_profile.uses_cloudflare_workers,
            templates=templates.monorepo_templates(self.environments, knowledge_profile, runtime_profile),
            smoke_commands=runtime_profile.smoke_commands,
        )

    def kustomize_template_configs(self) -> tuple[TemplateConfig, ...]:
        """Return Kubernetes Kustomize template mappings."""
        return templates.kustomize_template_configs()

    def helm_template_configs(self) -> tuple[TemplateConfig, ...]:
        """Return Helm chart template mappings."""
        return templates.helm_template_configs()

    def _monorepo_artifacts(self, runtime_profile: RuntimeProfile, *, helm: bool) -> tuple[str, str]:
        if runtime_profile.uses_kubernetes and runtime_profile.uses_cloudflare_workers:
            return ("helm+wrangler", "Helm and Wrangler") if helm else ("kustomize+wrangler", "Kustomize and Wrangler")
        if runtime_profile.uses_kubernetes:
            return ("helm", "Helm") if helm else ("kustomize", "Kustomize")
        return "wrangler", "Wrangler"

    def _normalize(self, value: str, profiles: Mapping[str, Profile]) -> str:
        candidate = value.strip().lower()
        if candidate in profiles:
            return candidate
        for profile in profiles.values():
            if candidate in profile.aliases:
                return profile.id
        return candidate


stack_registry = StackProfileRegistry()
