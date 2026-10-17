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
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.generator.backstage_render import (
    DEFAULT_LIFECYCLE as DEFAULT_LIFECYCLE,
    DEFAULT_OWNER as DEFAULT_OWNER,
    component_body,
    component_spec,
    system_body,
    system_spec,
    validation_issues,
)
from src.generator.markers import fence, find_fenced_region, replace_fenced_region
from src.generator.scaffold_contract import (
    MANIFEST_PATH,
    ParsedManifest,
    ScaffoldContract,
    load_parsed_manifest,
)
from src.utils.errors import KickstartError, ManifestShapeError, MarkerError

CATALOG_PATH = "catalog-info.yaml"

_ROOT_FENCE_ID = "catalog-derived"
_SYSTEM_FENCE_ID = "catalog-system"

# Backstage entity-name contract (metadata.name): the API rejects anything
# else, so validate before writing instead of emitting a doomed entity.
_BACKSTAGE_NAME = re.compile(r"[A-Za-z0-9][-A-Za-z0-9_.]*")
_BACKSTAGE_NAME_MAX_LENGTH = 63


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
    children = _children(resolved, manifest, name) if contract.project_kind == "system" else ()

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
        fence(_ROOT_FENCE_ID, component_body(contract, name, "dir:." if has_docs else None), style="yaml")
        + component_spec(contract, system=name if contract.project_kind == "system" else None)
    ]
    if contract.project_kind == "system":
        documents.append(fence(_SYSTEM_FENCE_ID, system_body(name), style="yaml") + system_spec())
        documents.extend(
            fence(child.fence_id, component_body(child.contract, child.name, child.techdocs_ref), style="yaml")
            + component_spec(child.contract, system=name)
            for child in children
        )
    content = "---\n".join(documents)
    _write_catalog(target, content)
    return BackstageExportResult(path=target, action="created", issues=validation_issues(content))


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
            text, _ROOT_FENCE_ID, component_body(contract, name, "dir:." if has_docs else None), style="yaml"
        )
        if contract.project_kind == "system":
            if find_fenced_region(updated, _SYSTEM_FENCE_ID, style="yaml"):
                updated = replace_fenced_region(updated, _SYSTEM_FENCE_ID, system_body(name), style="yaml")
            for child in children:
                if find_fenced_region(updated, child.fence_id, style="yaml"):
                    updated = replace_fenced_region(
                        updated,
                        child.fence_id,
                        component_body(child.contract, child.name, child.techdocs_ref),
                        style="yaml",
                    )
    except MarkerError as error:
        raise BackstageExportError(f"existing {CATALOG_PATH} has malformed kickstart fences: {error}") from error

    if updated == text:
        return BackstageExportResult(path=target, action="unchanged", issues=validation_issues(text))
    _write_catalog(target, updated)
    return BackstageExportResult(path=target, action="updated", issues=validation_issues(updated))


def _write_catalog(target: Path, content: str) -> None:
    try:
        target.write_text(content, encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BackstageExportError(f"cannot write {CATALOG_PATH}: {error}") from error


def _children(resolved: Path, manifest: ParsedManifest, root_name: str) -> tuple[_Child, ...]:
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
    for child_manifest_path in _child_paths(resolved, globs):
        try:
            child_manifest = load_parsed_manifest(child_manifest_path)
            child_contract = ScaffoldContract.from_manifest(child_manifest)
            child_name = _project_name(child_manifest)
        except ManifestShapeError:
            continue
        name_issue = _backstage_name_issue(child_name)
        if name_issue:
            raise BackstageExportError(f"contained project cannot be exported: {name_issue}")
        if child_name == root_name:
            raise BackstageExportError(f"contained project '{child_name}' duplicates the root Component name")
        fence_id = f"catalog-child-{_fence_safe(child_name)}"
        owner = fence_id_owners.get(fence_id)
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
        children.append(_Child(name=child_name, fence_id=fence_id, contract=child_contract, techdocs_ref=techdocs_ref))
    return tuple(children)


def _child_paths(root: Path, patterns: Sequence[object]) -> Iterator[Path]:
    """Yield each distinct child manifest once, retaining its original docs path."""
    try:
        root_manifest = (root / MANIFEST_PATH).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise BackstageExportUsageError(f"cannot inspect {MANIFEST_PATH}: {error}") from error
    seen = {root_manifest}
    for pattern in patterns:
        if not isinstance(pattern, str):
            continue
        for path in sorted(root.glob(pattern)):
            try:
                identity = path.resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if identity not in seen:
                seen.add(identity)
                yield path


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
