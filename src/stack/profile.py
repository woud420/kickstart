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
    "stack_registry",
]
