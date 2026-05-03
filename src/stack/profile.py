"""Compatibility exports for stack profile registry APIs."""

from src.stack.registry import StackProfileRegistry, stack_registry
from src.stack.types import (
    ArtifactToolProfile,
    CloudProfile,
    KnowledgeProfile,
    LanguageProfile,
    MonorepoSelection,
    RuntimeProfile,
    ServiceSelection,
    SystemSelection,
    TemplateConfig,
    WorkspaceToolingProfile,
)

__all__ = [
    "CloudProfile",
    "ArtifactToolProfile",
    "KnowledgeProfile",
    "LanguageProfile",
    "MonorepoSelection",
    "RuntimeProfile",
    "ServiceSelection",
    "StackProfileRegistry",
    "SystemSelection",
    "TemplateConfig",
    "WorkspaceToolingProfile",
    "stack_registry",
]
