"""Read-only docs drift plan: re-render managed docs and compare.

Scope wall (documented in ``docs/contracts/plan-drift-scope.md``): this module
covers exactly the registry-rendered markdown projections inside their
ownership fences. Broader envelope drift — Makefile targets, CI workflows,
artifact files — belongs to the schema-4.0 drift check; inserting fences into
pre-fence repos belongs to the adopt write path. Nothing here mutates the
repository.

Statuses per managed artifact:

- ``in-sync``: the fenced region matches a candidate render byte-for-byte.
- ``would-create``: the managed file is missing.
- ``content-drift``: the fenced region differs (a unified diff against the
  closest candidate render is attached).
- ``unfenced``: the file exists with no fence — a pre-fence scaffold or
  hand-written file; reported as a structural fact, content never compared.
- ``malformed-markers``: fail-closed marker parsing rejected the file.
- ``unreadable``: the file could not be read as UTF-8 text.
- ``presence-only``: the architecture README, whose content needs
  generation-time inputs (title, directory list) a schema-3.0 manifest never
  recorded; only its existence is checked.

A worker-kind manifest cannot say which language generated it (the schema-3.0
expressiveness gap), so worker repos are compared against both the TypeScript
worker docs profile and the default profile and match either.
"""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.generator.markers import find_fenced_region
from src.generator.projections import (
    ARCHITECTURE_README_ID,
    ARCHITECTURE_README_TARGET,
    PROFILE_DEFAULT,
    PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER,
    DocsProjection,
    ProjectionProfile,
    scaffold_docs_projections,
)
from src.generator.scaffold_contract import MANIFEST_PATH, ScaffoldContract, load_parsed_manifest
from src.utils.errors import KickstartError, ManifestShapeError, MarkerError

PlanStatus = Literal[
    "in-sync",
    "presence-only",
    "would-create",
    "content-drift",
    "unfenced",
    "malformed-markers",
    "unreadable",
]

_MISSING_DETAIL = "managed file missing"


class DocsPlanTargetError(KickstartError):
    """Raised when the target repo or its manifest cannot be planned against."""


@dataclass(frozen=True)
class DocsPlanEntry:
    """Plan result for one managed docs artifact."""

    artifact_id: str
    target: str
    status: PlanStatus
    detail: str = ""
    diff: str = ""
    profile: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("in-sync", "presence-only")


@dataclass(frozen=True)
class DocsPlanReport:
    """Result of a read-only docs plan."""

    root: Path
    entries: tuple[DocsPlanEntry, ...]

    @property
    def in_sync(self) -> bool:
        return all(entry.ok for entry in self.entries)

    def to_json(self) -> str:
        """Machine-readable report for agents and CI."""
        payload = {
            "root": str(self.root),
            "in_sync": self.in_sync,
            "entries": [
                {
                    "artifact": entry.artifact_id,
                    "target": entry.target,
                    "status": entry.status,
                    "detail": entry.detail,
                    "diff": entry.diff,
                    "profile": entry.profile,
                }
                for entry in self.entries
            ],
        }
        return json.dumps(payload, indent=2) + "\n"


def inspect_docs(root: Path) -> DocsPlanReport:
    """Plan the managed docs of an existing repository, read-only."""
    if not root.is_dir():
        raise DocsPlanTargetError(f"plan target '{root}' is not an existing directory")
    resolved = root.resolve()

    contract = _contract_from_repo(resolved)
    profiles = _candidate_profiles(contract)
    renders = tuple(scaffold_docs_projections(contract, profile) for profile in profiles)

    entries = [
        _plan_entry(resolved, profiles, variants)
        for variants in zip(*renders, strict=True)
    ]
    entries.append(_architecture_entry(resolved))
    return DocsPlanReport(root=resolved, entries=tuple(entries))


def _contract_from_repo(resolved: Path) -> ScaffoldContract:
    try:
        parsed = load_parsed_manifest(resolved / MANIFEST_PATH)
        return ScaffoldContract.from_manifest(parsed)
    except ManifestShapeError as error:
        raise DocsPlanTargetError(f"cannot plan against {MANIFEST_PATH}: {error}") from error


def _candidate_profiles(contract: ScaffoldContract) -> tuple[ProjectionProfile, ...]:
    # Schema 3.0 never recorded worker language, so a worker manifest is
    # ambiguous between the TS worker docs profile and the default docs a
    # Rust worker gets; accept a byte-exact match against either.
    if contract.project_kind == "worker":
        return (PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER, PROFILE_DEFAULT)
    return (PROFILE_DEFAULT,)


def _plan_entry(
    resolved: Path,
    profiles: tuple[ProjectionProfile, ...],
    variants: tuple[DocsProjection, ...],
) -> DocsPlanEntry:
    projection = variants[0]
    path = resolved / projection.target
    if not path.is_file():
        return DocsPlanEntry(projection.id, projection.target, "would-create", detail=_MISSING_DETAIL)

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return DocsPlanEntry(projection.id, projection.target, "unreadable", detail=str(error))

    try:
        region = find_fenced_region(text, projection.id)
    except MarkerError as error:
        return DocsPlanEntry(projection.id, projection.target, "malformed-markers", detail=str(error))
    if region is None:
        return DocsPlanEntry(
            projection.id,
            projection.target,
            "unfenced",
            detail="no ownership fence (pre-fence scaffold or hand-written file); content not compared",
        )

    for profile, variant in zip(profiles, variants, strict=True):
        if region.inner == variant.body:
            return DocsPlanEntry(projection.id, projection.target, "in-sync", profile=profile)

    # Diff against the closest candidate so the report shows the real drift
    # instead of a wholesale replacement against an arbitrary profile.
    candidate_diffs = [
        (_unified_diff(variant.body, region.inner, projection.target), profile)
        for profile, variant in zip(profiles, variants, strict=True)
    ]
    diff, profile = min(candidate_diffs, key=lambda pair: len(pair[0]))
    detail = "owned region differs from the current standard's render"
    if len(profiles) > 1:
        detail += f" (closest candidate profile: {profile})"
    return DocsPlanEntry(projection.id, projection.target, "content-drift", detail=detail, diff=diff)


def _unified_diff(expected: str, actual: str, target: str) -> str:
    return "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=f"expected/{target}",
            tofile=f"actual/{target}",
        )
    )


def _architecture_entry(resolved: Path) -> DocsPlanEntry:
    if (resolved / ARCHITECTURE_README_TARGET).is_file():
        return DocsPlanEntry(
            ARCHITECTURE_README_ID,
            ARCHITECTURE_README_TARGET,
            "presence-only",
            detail=(
                "content needs generation-time inputs (title, directory list) a schema-3.0 "
                "manifest does not record; presence checked only"
            ),
        )
    return DocsPlanEntry(
        ARCHITECTURE_README_ID, ARCHITECTURE_README_TARGET, "would-create", detail=_MISSING_DETAIL
    )
