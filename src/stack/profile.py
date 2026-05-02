"""Compatibility exports for stack profile registry APIs."""

from src.stack.registry import StackProfileRegistry, stack_registry
from src.stack.types import (
    CloudProfile,
    DeploymentToolProfile,
    KnowledgeProfile,
    LanguageProfile,
    MonorepoSelection,
    RuntimeProfile,
    ServiceSelection,
    TemplateConfig,
)

__all__ = [
    "CloudProfile",
    "DeploymentToolProfile",
    "KnowledgeProfile",
    "LanguageProfile",
    "MonorepoSelection",
    "RuntimeProfile",
    "ServiceSelection",
    "StackProfileRegistry",
    "TemplateConfig",
    "stack_registry",
]
