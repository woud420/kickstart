"""Deterministic Backstage catalog export derived from scaffold state.

`kickstart export backstage` emits `catalog-info.yaml` from
`.kickstart/scaffold.json` with three field classes
(``docs/contracts/backstage-export.md``):

- **derived** — apiVersion, kind, metadata (name, techdocs annotation, tags)
  and, for systems, the System entity and one child Component per contained
  project. Derived lines live inside ``# kickstart:begin/end`` YAML fences and
  are refreshed on every export (including the fences of children that still
  resolve; children added after creation are not auto-inserted).
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

import re
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

# One anonymous-default constant for the --knowledge backstage templates, this
# exporter, and the backstage-catalog skill. Backstage rejects entities
# without owner and lifecycle, so unknown values get valid sentinels instead
# of empties.
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

_COMPONENT_REQUIRED_LINES = ("apiVersion:", "kind:", "name:", "type:", "lifecycle:", "owner:")
_SYSTEM_REQUIRED_LINES = ("apiVersion:", "kind:", "name:", "owner:")

# Conservative plain-scalar shape: values matching this parse back as the
# same string under YAML. ':' is only allowed when followed by another safe
# character (YAML treats ':' as special only before whitespace/end), which
# keeps `group:default/unknown` and `dir:./apps/x` unquoted. Reserved words
# and leading digits are quoted so `null` or `123` stay strings.
_PLAIN_YAML_SAFE = re.compile(r"[A-Za-z][A-Za-z0-9._/-]*(?::[A-Za-z0-9._/-]+)*")
_YAML_RESERVED = frozenset(
    {"null", "~", "true", "false", "yes", "no", "on", "off", "y", "n"}
)

# Backstage entity-name contract (metadata.name): the API rejects anything
# else, so validate before writing instead of emitting a doomed entity.
_BACKSTAGE_NAME = re.compile(r"[A-Za-z0-9][-A-Za-z0-9_.]*")
_BACKSTAGE_NAME_MAX_LENGTH = 63


def _yaml_string(value: str) -> str:
    """Render a string as a YAML scalar that always parses back as a string."""
    if _PLAIN_YAML_SAFE.fullmatch(value) and value.lower() not in _YAML_RESERVED:
        return value
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _backstage_name_issue(name: str) -> str:
    """Return why a name violates the Backstage metadata.name contract, or ''."""
    if len(name) > _BACKSTAGE_NAME_MAX_LENGTH:
        return f"'{name}' is longer than the {_BACKSTAGE_NAME_MAX_LENGTH}-character Backstage limit"
    if _BACKSTAGE_NAME.fullmatch(name) is None:
        return f"'{name}' is not a valid Backstage entity name"
    return ""


class BackstageExportError(KickstartError):
    """Raised when an export is refused (unfenced or unreadable target)."""


class BackstageExportUsageError(BackstageExportError):
    """Raised when there is nothing usable to export from (exit-2 class)."""


@dataclass(frozen=True)
class _Child:
    """One contained project resolved from the system's composition globs."""

    name: str
    fence_id: str
    contract: ScaffoldContract
    techdocs_ref: str | None


@dataclass(frozen=True)
class BackstageExportResult:
    """Outcome of one export run."""

    path: Path
    action: Literal["created", "updated", "unchanged"]
    issues: tuple[str, ...] = ()


def export_backstage(root: Path) -> BackstageExportResult:
    """Write or refresh the repo's catalog entities, derived fields only."""
    if not root.is_dir():
        raise BackstageExportUsageError(f"export target '{root}' is not an existing directory")
    resolved = root.resolve()

    try:
        manifest = load_parsed_manifest(resolved / MANIFEST_PATH)
        contract = ScaffoldContract.from_manifest(manifest)
        name = _project_name(manifest)
    except ManifestShapeError as error:
        raise BackstageExportUsageError(f"cannot export from {MANIFEST_PATH}: {error}") from error
    name_issue = _backstage_name_issue(name)
    if name_issue:
        raise BackstageExportUsageError(f"cannot export {MANIFEST_PATH}: {name_issue}")
    has_docs = (resolved / "docs").is_dir()
    children = _children(resolved, manifest) if contract.project_kind == "system" else ()

    target = resolved / CATALOG_PATH
    if target.exists() or target.is_symlink():
        return _refresh(target, contract, name, has_docs, children)
    return _create(target, contract, name, has_docs, children)


def _create(
    target: Path,
    contract: ScaffoldContract,
    name: str,
    has_docs: bool,
    children: tuple[_Child, ...],
) -> BackstageExportResult:
    documents = [
        fence(_ROOT_FENCE_ID, _component_derived_body(contract, name, "dir:." if has_docs else None), style="yaml")
        + _spec_block(contract, system=name if contract.project_kind == "system" else None)
    ]
    if contract.project_kind == "system":
        documents.append(fence(_SYSTEM_FENCE_ID, _system_derived_body(name), style="yaml") + _spec_block_system())
        documents.extend(
            fence(child.fence_id, _component_derived_body(child.contract, child.name, child.techdocs_ref), style="yaml")
            + _spec_block(child.contract, system=name)
            for child in children
        )
    content = "---\n".join(documents)
    target.write_text(content, encoding="utf-8")
    return BackstageExportResult(path=target, action="created", issues=_validation_issues(content))


def _refresh(
    target: Path,
    contract: ScaffoldContract,
    name: str,
    has_docs: bool,
    children: tuple[_Child, ...],
) -> BackstageExportResult:
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise BackstageExportError(f"cannot read existing {CATALOG_PATH}: {error}") from error

    try:
        region = find_fenced_region(text, _ROOT_FENCE_ID, style="yaml")
        if region is None:
            raise BackstageExportError(
                f"existing {CATALOG_PATH} has no kickstart fence; refusing to modify a hand-written file"
            )

        updated = replace_fenced_region(
            text, _ROOT_FENCE_ID, _component_derived_body(contract, name, "dir:." if has_docs else None), style="yaml"
        )
        if contract.project_kind == "system":
            if find_fenced_region(updated, _SYSTEM_FENCE_ID, style="yaml"):
                updated = replace_fenced_region(updated, _SYSTEM_FENCE_ID, _system_derived_body(name), style="yaml")
            for child in children:
                if find_fenced_region(updated, child.fence_id, style="yaml"):
                    updated = replace_fenced_region(
                        updated,
                        child.fence_id,
                        _component_derived_body(child.contract, child.name, child.techdocs_ref),
                        style="yaml",
                    )
    except MarkerError as error:
        raise BackstageExportError(f"existing {CATALOG_PATH} has malformed kickstart fences: {error}") from error

    if updated == text:
        return BackstageExportResult(path=target, action="unchanged", issues=_validation_issues(text))
    target.write_text(updated, encoding="utf-8")
    return BackstageExportResult(path=target, action="updated", issues=_validation_issues(updated))


def _component_derived_body(contract: ScaffoldContract, name: str, techdocs_ref: str | None) -> str:
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


def _system_derived_body(name: str) -> str:
    return "\n".join(
        [
            "apiVersion: backstage.io/v1alpha1",
            "kind: System",
            "metadata:",
            f"  name: {_yaml_string(name)}",
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
        lines.append(f"  system: {_yaml_string(system)}")
    return "\n".join(lines) + "\n"


def _spec_block_system() -> str:
    return "\n".join(["spec:", f"  owner: {DEFAULT_OWNER}"]) + "\n"


def _children(resolved: Path, manifest: ParsedManifest) -> tuple[_Child, ...]:
    """Contained projects resolved from the system's composition globs.

    Children that cannot be interpreted (unparseable manifest, missing name)
    are skipped rather than aborting the export. Children that would export
    wrongly — an invalid Backstage name, or two names colliding onto one
    fence id — abort loudly instead of silently dropping an entity.
    """
    composition = manifest.get("composition")
    if not isinstance(composition, dict):
        return ()
    globs = composition.get("child_manifest_globs")
    if not isinstance(globs, list):
        return ()

    children: list[_Child] = []
    fence_id_owners: dict[str, str] = {}
    for pattern in globs:
        if not isinstance(pattern, str):
            continue
        for child_manifest_path in sorted(resolved.glob(pattern)):
            try:
                child_manifest = load_parsed_manifest(child_manifest_path)
                child_contract = ScaffoldContract.from_manifest(child_manifest)
                child_name = _project_name(child_manifest)
            except ManifestShapeError:
                continue
            name_issue = _backstage_name_issue(child_name)
            if name_issue:
                raise BackstageExportError(f"contained project cannot be exported: {name_issue}")
            fence_id = f"catalog-child-{_fence_safe(child_name)}"
            owner = fence_id_owners.get(fence_id)
            if owner == child_name:
                # The same child discovered through overlapping globs.
                continue
            if owner is not None:
                # Silently dropping an entity would break the promised
                # one-Component-per-child mapping; fail loudly instead.
                raise BackstageExportError(
                    f"contained projects '{owner}' and '{child_name}' both map to fence id "
                    f"'{fence_id}'; rename one so every child keeps its own catalog entity"
                )
            fence_id_owners[fence_id] = child_name
            child_root = child_manifest_path.parent.parent
            techdocs_ref: str | None = None
            if (child_root / "docs").is_dir():
                # Entities in the root catalog file resolve relative paths
                # against the root, so each child needs its own subpath.
                techdocs_ref = f"dir:./{child_root.relative_to(resolved).as_posix()}"
            children.append(
                _Child(name=child_name, fence_id=fence_id, contract=child_contract, techdocs_ref=techdocs_ref)
            )
    return tuple(children)


def _fence_safe(name: str) -> str:
    """Map a project name onto the marker id alphabet (underscores allowed in names)."""
    return re.sub(r"[^a-z0-9-]", "-", name)


def _project_name(manifest: ParsedManifest) -> str:
    project = manifest.get("project")
    if isinstance(project, dict):
        name = project.get("name")
        if isinstance(name, str) and name:
            return name
    raise ManifestShapeError("manifest has no project.name to derive the entity name from")


def _tags(contract: ScaffoldContract) -> list[str]:
    extensions = contract.service_extensions
    extension_values = [
        value for value in (extensions.database, extensions.cache, extensions.auth) if value is not None
    ]
    return sorted({*extension_values, *contract.execution_models})


def _validation_issues(content: str) -> tuple[str, ...]:
    """Per-entity line-presence validation for the fields Backstage requires."""
    issues: list[str] = []
    for index, document in enumerate(content.split("\n---\n")):
        required_lines = _SYSTEM_REQUIRED_LINES if "kind: System" in document else _COMPONENT_REQUIRED_LINES
        for required in required_lines:
            if not any(line.strip().startswith(required) for line in document.splitlines()):
                issues.append(f"entity {index + 1} missing required field line: {required}")
    return tuple(issues)
