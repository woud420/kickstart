"""Typed template plans for generator rendering."""

from dataclasses import dataclass, field
from typing import Iterable

from src.stack.types import TemplateConfig
from src.utils.types import TemplateValue, TemplateVars


@dataclass(frozen=True)
class TemplatePlanEntry:
    """Resolved template render instruction."""

    target: str
    template: str
    vars: dict[str, TemplateValue]


@dataclass(frozen=True)
class TemplatePlan:
    """A typed plan for rendering project templates."""

    templates: tuple[TemplateConfig, ...]
    base_vars: TemplateVars = field(default_factory=dict)

    @classmethod
    def from_templates(
        cls,
        templates: Iterable[TemplateConfig],
        base_vars: TemplateVars | None = None,
    ) -> "TemplatePlan":
        """Create a plan from template configs and optional shared variables."""
        return cls(tuple(templates), dict(base_vars or {}))

    def entries(self) -> tuple[TemplatePlanEntry, ...]:
        """Return template entries with shared and per-template variables merged."""
        entries: list[TemplatePlanEntry] = []
        for template in self.templates:
            template_vars = dict(self.base_vars)
            template_vars.update(template.vars)
            entries.append(
                TemplatePlanEntry(
                    target=template.target,
                    template=template.template,
                    vars=template_vars,
                )
            )
        return tuple(entries)
