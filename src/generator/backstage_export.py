"""Deterministic Backstage catalog export derived from scaffold state.

`kickstart export backstage` emits `catalog-info.yaml` from
`.kickstart/scaffold.json` with three field classes
(``docs/contracts/backstage-export.md``):

- **derived** — apiVersion, kind, metadata (name, techdocs annotation, tags)
  and, for systems, the System entity and one child Component per contained
  project. Derived lines live inside ``# kickstart:begin/end`` YAML fences and
  are refreshed on every export.
- **declared** — ``spec.type``, ``spec.lifecycle``, ``spec.owner`` (and any
  description the user adds): emitted once with anonymous, catalog-valid
  defaults, then user-owned. Backstage requires owner and lifecycle to exist,
  so the defaults are sentinels, never empty values.
- **passthrough** — everything else outside the fences is never read for
  decisions and never rewritten.

Re-export replaces only the fenced regions, so repeated exports are
idempotent and user edits outside fences always survive. An existing
`catalog-info.yaml` without a kickstart fence is refused, never overwritten.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.generator.markers import fence, find_fenced_region, replace_fenced_region
from src.generator.scaffold_contract import (
    MANIFEST_PATH,
    ParsedManifest,
    ScaffoldContract,
    load_parsed_manifest,
)
from src.utils.errors import KickstartError, ManifestShapeError, MarkerError

CATALOG_PATH = "catalog-info.yaml"

# One anonymous-default constant for the system template, this exporter, and
# the backstage-catalog skill. Backstage rejects entities without owner and
# lifecycle, so unknown values get valid sentinels instead of empties.
DEFAULT_OWNER = "group:default/unknown"
DEFAULT_LIFECYCLE = "experimental"

_ROOT_FENCE_ID = "catalog-derived"
_SYSTEM_FENCE_ID = "catalog-system"

_SPEC_TYPES: dict[str, str] = {
    "service": "service",
    "worker": "service",
    "frontend": "website",
    "library": "library",
    "cli": "tool",
    "system": "system",
}

_REQUIRED_LINES = ("apiVersion:", "kind:", "name:", "type:", "lifecycle:", "owner:")


class BackstageExportError(KickstartError):
    """Raised when the repo cannot be exported (no manifest, unfenced file)."""


@dataclass(frozen=True)
class BackstageExportResult:
    """Outcome of one export run."""

    path: Path
    action: Literal["created", "updated", "unchanged"]
    issues: tuple[str, ...] = ()


def export_backstage(root: Path) -> BackstageExportResult:
    """Write or refresh the repo's catalog entities, derived fields only."""
    if not root.is_dir():
        raise BackstageExportError(f"export target '{root}' is not an existing directory")
    resolved = root.resolve()

    try:
        manifest = load_parsed_manifest(resolved / MANIFEST_PATH)
        contract = ScaffoldContract.from_manifest(manifest)
    except ManifestShapeError as error:
        raise BackstageExportError(f"cannot export from {MANIFEST_PATH}: {error}") from error
    name = _project_name(manifest)
    has_docs = (resolved / "docs").is_dir()

    target = resolved / CATALOG_PATH
    if target.exists():
        result = _refresh(target, contract, name, has_docs)
    else:
        result = _create(target, resolved, contract, manifest, name, has_docs)
    return result


def _create(
    target: Path,
    resolved: Path,
    contract: ScaffoldContract,
    manifest: ParsedManifest,
    name: str,
    has_docs: bool,
) -> BackstageExportResult:
    documents = [
        fence(_ROOT_FENCE_ID, _component_derived_body(contract, name, has_docs), style="yaml")
        + _spec_block(contract, system=name if contract.project_kind == "system" else None)
    ]
    if contract.project_kind == "system":
        documents.append(fence(_SYSTEM_FENCE_ID, _system_derived_body(name), style="yaml") + _spec_block_system())
        documents.extend(_child_documents(resolved, manifest, name))
    content = "---\n".join(documents)
    target.write_text(content, encoding="utf-8")
    return BackstageExportResult(path=target, action="created", issues=_validation_issues(content))


def _refresh(target: Path, contract: ScaffoldContract, name: str, has_docs: bool) -> BackstageExportResult:
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise BackstageExportError(f"cannot read existing {CATALOG_PATH}: {error}") from error

    try:
        region = find_fenced_region(text, _ROOT_FENCE_ID, style="yaml")
    except MarkerError as error:
        raise BackstageExportError(f"existing {CATALOG_PATH} has malformed kickstart fences: {error}") from error
    if region is None:
        raise BackstageExportError(
            f"existing {CATALOG_PATH} has no kickstart fence; refusing to modify a hand-written file"
        )

    updated = replace_fenced_region(
        text, _ROOT_FENCE_ID, _component_derived_body(contract, name, has_docs), style="yaml"
    )
    if contract.project_kind == "system" and find_fenced_region(updated, _SYSTEM_FENCE_ID, style="yaml"):
        updated = replace_fenced_region(updated, _SYSTEM_FENCE_ID, _system_derived_body(name), style="yaml")

    if updated == text:
        return BackstageExportResult(path=target, action="unchanged", issues=_validation_issues(text))
    target.write_text(updated, encoding="utf-8")
    return BackstageExportResult(path=target, action="updated", issues=_validation_issues(updated))


def _component_derived_body(contract: ScaffoldContract, name: str, has_docs: bool) -> str:
    lines = [
        "apiVersion: backstage.io/v1alpha1",
        "kind: Component",
        "metadata:",
        f"  name: {name}",
    ]
    if has_docs:
        lines.extend(["  annotations:", "    backstage.io/techdocs-ref: dir:."])
    tags = _tags(contract)
    if tags:
        lines.append("  tags:")
        lines.extend(f"    - {tag}" for tag in tags)
    return "\n".join(lines) + "\n"


def _system_derived_body(name: str) -> str:
    return "\n".join(
        [
            "apiVersion: backstage.io/v1alpha1",
            "kind: System",
            "metadata:",
            f"  name: {name}",
        ]
    ) + "\n"


def _spec_block(contract: ScaffoldContract, system: str | None = None) -> str:
    lines = [
        "spec:",
        f"  type: {_SPEC_TYPES[contract.project_kind]}",
        f"  lifecycle: {DEFAULT_LIFECYCLE}",
        f"  owner: {DEFAULT_OWNER}",
    ]
    if system is not None:
        lines.append(f"  system: {system}")
    return "\n".join(lines) + "\n"


def _spec_block_system() -> str:
    return "\n".join(["spec:", f"  owner: {DEFAULT_OWNER}"]) + "\n"


def _child_documents(resolved: Path, manifest: ParsedManifest, system_name: str) -> list[str]:
    """Creation-time Component docs for contained projects, one per child manifest."""
    composition = manifest.get("composition")
    if not isinstance(composition, dict):
        return []
    globs = composition.get("child_manifest_globs")
    if not isinstance(globs, list):
        return []

    documents: list[str] = []
    seen: set[str] = set()
    for pattern in globs:
        if not isinstance(pattern, str):
            continue
        for child_manifest_path in sorted(resolved.glob(pattern)):
            try:
                child_manifest = load_parsed_manifest(child_manifest_path)
                child_contract = ScaffoldContract.from_manifest(child_manifest)
            except ManifestShapeError:
                continue
            child_name = _project_name(child_manifest)
            if child_name in seen:
                continue
            seen.add(child_name)
            child_root = child_manifest_path.parent.parent
            body = _component_derived_body(child_contract, child_name, (child_root / "docs").is_dir())
            documents.append(
                fence(f"catalog-child-{child_name}", body, style="yaml")
                + _spec_block(child_contract, system=system_name)
            )
    return documents


def _project_name(manifest: ParsedManifest) -> str:
    project = manifest.get("project")
    if isinstance(project, dict):
        name = project.get("name")
        if isinstance(name, str) and name:
            return name
    raise BackstageExportError("manifest has no project.name to derive the entity name from")


def _tags(contract: ScaffoldContract) -> list[str]:
    extensions = contract.service_extensions
    extension_values = [
        value for value in (extensions.database, extensions.cache, extensions.auth) if value is not None
    ]
    return sorted({*extension_values, *contract.execution_models})


def _validation_issues(content: str) -> tuple[str, ...]:
    """Line-presence validation for the fields Backstage requires."""
    issues: list[str] = []
    for required in _REQUIRED_LINES:
        if not any(line.strip().startswith(required) for line in content.splitlines()):
            issues.append(f"missing required field line: {required}")
    return tuple(issues)
