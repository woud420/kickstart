"""Typed stack profile models."""

from dataclasses import dataclass, field
from typing import Mapping

from src.utils.types import TemplateConfigDict, TemplatePathConfig, TemplateVars


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

    def as_plain_dict(self) -> TemplatePathConfig:
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
    artifact_tools: tuple[str, ...] = ()
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
class ArtifactToolProfile:
    """Generated artifact tool metadata."""

    id: str
    display_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ServiceSelection:
    """Validated service scaffold selection."""

    language: str
    runtime: str
    artifact_tool: str
    templates: tuple[TemplateConfig, ...]
    smoke_commands: tuple[str, ...]

    def template_configs(self) -> list[TemplatePathConfig]:
        """Return generator-compatible template configs."""
        return [template.as_plain_dict() for template in self.templates]


@dataclass(frozen=True)
class MonorepoSelection:
    """Validated monorepo scaffold selection."""

    cloud: str
    clouds: tuple[str, ...]
    knowledge: str
    runtime: str
    artifact_tool: str
    artifact_label: str
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


Profile = LanguageProfile | RuntimeProfile | CloudProfile | KnowledgeProfile | ArtifactToolProfile
