"""Shared type aliases for generator configuration and template rendering."""

from typing import Mapping
from typing import TypedDict

ConfigValue = str | int | float | bool | None | list[str] | dict[str, str]
GeneratorConfig = Mapping[str, ConfigValue]

RenderValue = ConfigValue
RenderVars = Mapping[str, RenderValue]
MutableRenderVars = dict[str, RenderValue]

TemplateValue = str | bool | list[str]
TemplateVars = Mapping[str, TemplateValue]
TemplateConfigValue = str | TemplateVars
TemplateConfigMapping = Mapping[str, TemplateConfigValue]


class TemplatePathConfig(TypedDict):
    """Template target/source mapping without render variables."""

    target: str
    template: str


class TemplateConfigDict(TemplatePathConfig, total=False):
    """Template target/source mapping with optional render variables."""

    vars: TemplateVars

ErrorContextValue = str | int | float | bool | None
ErrorContext = Mapping[str, ErrorContextValue]
MutableErrorContext = dict[str, ErrorContextValue]
