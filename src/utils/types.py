"""Shared type aliases for generator configuration and template rendering."""

from typing import Mapping

ConfigValue = str | int | float | bool | None | list[str] | dict[str, str]
GeneratorConfig = Mapping[str, ConfigValue]

TemplateValue = str | bool | list[str]
TemplateVars = Mapping[str, TemplateValue]
TemplateConfigValue = str | TemplateVars
TemplateConfigMapping = Mapping[str, TemplateConfigValue]
TemplateConfigDict = dict[str, str | dict[str, TemplateValue]]
