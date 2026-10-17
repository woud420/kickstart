"""Pure catalog rendering, scalar encoding and required-line checks."""

import re

import yaml

from src.generator.scaffold_contract import ScaffoldContract

DEFAULT_OWNER = "group:default/unknown"
DEFAULT_LIFECYCLE = "experimental"

_SPEC_TYPES: dict[str, str] = {
    "service": "service",
    "worker": "service",
    "frontend": "website",
    "library": "library",
    "cli": "tool",
    "system": "system",
}
_COMPONENT_REQUIRED_LINES = ("apiVersion:", "kind:", "name:", "type:", "lifecycle:", "owner:")
_SYSTEM_REQUIRED_LINES = ("apiVersion:", "kind:", "name:", "owner:")

# Unquoted values must survive YAML's implicit scalar conversions.
_PLAIN_YAML_SAFE = re.compile(r"[A-Za-z][A-Za-z0-9._/-]*(?::[A-Za-z0-9._/-]+)*")
_YAML_RESERVED = frozenset({"null", "~", "true", "false", "yes", "no", "on", "off", "y", "n"})


def _yaml_string(value: str) -> str:
    """Keep ordinary scalars readable and escape YAML controls and line separators."""
    if _PLAIN_YAML_SAFE.fullmatch(value) and value.lower() not in _YAML_RESERVED:
        return value
    return yaml.safe_dump(value, allow_unicode=True, default_style='"', width=2**31 - 1).rstrip("\n")


def component_body(contract: ScaffoldContract, name: str, techdocs_ref: str | None) -> str:
    lines = [
        "apiVersion: backstage.io/v1alpha1",
        "kind: Component",
        "metadata:",
        f"  name: {_yaml_string(name)}",
    ]
    if techdocs_ref is not None:
        lines.extend(["  annotations:", f"    backstage.io/techdocs-ref: {_yaml_string(techdocs_ref)}"])
    tags = _tags(contract)
    if tags:
        lines.append("  tags:")
        lines.extend(f"    - {_yaml_string(tag)}" for tag in tags)
    return "\n".join(lines) + "\n"


def system_body(name: str) -> str:
    return (
        "\n".join(
            [
                "apiVersion: backstage.io/v1alpha1",
                "kind: System",
                "metadata:",
                f"  name: {_yaml_string(name)}",
            ]
        )
        + "\n"
    )


def component_spec(contract: ScaffoldContract, system: str | None = None) -> str:
    lines = [
        "spec:",
        f"  type: {_SPEC_TYPES[contract.project_kind]}",
        f"  lifecycle: {DEFAULT_LIFECYCLE}",
        f"  owner: {DEFAULT_OWNER}",
    ]
    if system is not None:
        lines.append(f"  system: {_yaml_string(system)}")
    return "\n".join(lines) + "\n"


def system_spec() -> str:
    return "\n".join(["spec:", f"  owner: {DEFAULT_OWNER}"]) + "\n"


def _tags(contract: ScaffoldContract) -> list[str]:
    extensions = contract.service_extensions
    extension_values = [
        value for value in (extensions.database, extensions.cache, extensions.auth) if value is not None
    ]
    return sorted({*extension_values, *contract.execution_models})


def validation_issues(content: str) -> tuple[str, ...]:
    """Per-entity line-presence validation for the fields Backstage requires."""
    issues: list[str] = []
    for index, document in enumerate(content.split("\n---\n")):
        required_lines = _SYSTEM_REQUIRED_LINES if "kind: System" in document else _COMPONENT_REQUIRED_LINES
        for required in required_lines:
            if not any(line.strip().startswith(required) for line in document.splitlines()):
                issues.append(f"entity {index + 1} missing required field line: {required}")
    return tuple(issues)
