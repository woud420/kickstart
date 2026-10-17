"""Pure renderers for the external I/O exporter contract."""

from dataclasses import asdict
import json
import re

from src.generator.external_io_contract import (
    CliSurface,
    ConfigSurface,
    ExternalIOContract,
    FileSurface,
    HttpSurface,
    KnownSurface,
    SourceEvidence,
)


def render_external_io_json(contract: ExternalIOContract) -> str:
    """Render versioned data with stable keys, preserving observation order."""
    return json.dumps(asdict(contract), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _code(value: str) -> str:
    fence = "`" * (max((len(run) for run in re.findall(r"`+", value)), default=0) + 1)
    return f"{fence} {value} {fence}"


def _describe(surface: KnownSurface) -> str:
    if isinstance(surface, HttpSurface):
        return f"{surface.method} {surface.path}"
    if isinstance(surface, CliSurface):
        return " ".join((*surface.command, *((surface.option,) if surface.option else ())))
    if isinstance(surface, FileSurface):
        return f"{surface.access} {surface.path}"
    if isinstance(surface, ConfigSurface):
        required = "unknown" if surface.required is None else str(surface.required).lower()
        return f"{surface.source} {surface.name} (required={required})"
    return f"{surface.direction} {surface.protocol} {surface.endpoint}"


def _citation(evidence: SourceEvidence) -> str:
    lines = str(evidence.start_line)
    if evidence.end_line is not None and evidence.end_line != evidence.start_line:
        lines += f"-{evidence.end_line}"
    return _code(f"{evidence.path}:{lines}")


def render_external_io_markdown(contract: ExternalIOContract) -> str:
    """Render a source-cited section; empty unknowns never imply completeness."""
    lines = [
        "## External I/O",
        "",
        f"Project: {_code(contract.project)}.",
        f"Schema: {contract.schema_version}. Coverage: {contract.coverage}.",
        "",
        "### Observed surfaces",
        "",
    ]
    for observation in contract.surfaces:
        citations = ", ".join(_citation(evidence) for evidence in observation.evidence)
        lines.append(f"- {observation.surface.kind}: {_code(_describe(observation.surface))}; evidence: {citations}.")
    if not contract.surfaces:
        lines.append("No observed surfaces supplied.")
    lines.extend(("", "### Unknowns", ""))
    for unknown in contract.unknowns:
        lines.append(f"- {unknown.category}: {_code(unknown.reason)}.")
    if not contract.unknowns:
        lines.append("None recorded; coverage remains partial.")
    return "\n".join(lines) + "\n"
