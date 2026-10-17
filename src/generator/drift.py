"""Classed, read-only drift reporting within persisted scaffold ownership."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal, TypedDict

from src.generator.artifact_checks import owned_target
from src.generator.ownership_check import OwnershipEntry, inspect_ownership
from src.generator.workflow_check import inspect_workflow
from src.utils.errors import DriftTargetError, OwnershipPlanTargetError


ArtifactClass = Literal["scaffold", "docs", "ci", "artifact"]
DriftStatus = Literal["in-sync", "presence-only", "missing", "changed", "stale", "unreadable"]

DriftEntryPayload = TypedDict(
    "DriftEntryPayload",
    {"class": ArtifactClass, "target": str, "status": DriftStatus, "check": str, "detail": str, "diff": str},
)


class DriftPayload(TypedDict):
    root: str
    recorded: bool
    in_sync: bool
    seeds_excluded: int
    detail: str
    entries: list[DriftEntryPayload]


@dataclass(frozen=True)
class DriftEntry:
    artifact_class: ArtifactClass
    target: str
    status: DriftStatus
    check: str
    detail: str = ""
    diff: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {"in-sync", "presence-only"}

    def payload(self) -> DriftEntryPayload:
        return {
            "class": self.artifact_class,
            "target": self.target,
            "status": self.status,
            "check": self.check,
            "detail": self.detail,
            "diff": self.diff,
        }


@dataclass(frozen=True)
class DriftReport:
    root: Path
    recorded: bool
    entries: tuple[DriftEntry, ...] = ()
    seeds_excluded: int = 0

    @property
    def in_sync(self) -> bool:
        return self.recorded and all(entry.ok for entry in self.entries)

    def payload(self) -> DriftPayload:
        return {
            "root": str(self.root),
            "recorded": self.recorded,
            "in_sync": self.in_sync,
            "seeds_excluded": self.seeds_excluded,
            "detail": "" if self.recorded else "Ownership is unrecorded; drift coverage is unavailable.",
            "entries": [entry.payload() for entry in self.entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.payload(), indent=2) + "\n"


def _artifact_class(target: str) -> ArtifactClass:
    if target.startswith(".github/workflows/"):
        return "ci"
    if target.startswith("docs/"):
        return "docs"
    if target in {"Makefile"}:
        return "artifact"
    return "scaffold"


def _status(entry: OwnershipEntry) -> DriftStatus:
    if entry.status == "would-create":
        return "missing"
    if entry.status == "content-drift":
        return "changed"
    if entry.status in {"unfenced", "malformed-markers", "structural-gap"}:
        return "stale"
    if entry.status == "in-sync":
        return "in-sync"
    if entry.status == "presence-only":
        return "presence-only"
    if entry.status == "unreadable":
        return "unreadable"
    raise DriftTargetError(f"unsupported ownership finding: {entry.status}")


def _drift_entry(root: Path, entry: OwnershipEntry) -> DriftEntry:
    result = DriftEntry(
        _artifact_class(entry.target), entry.target, _status(entry), entry.check, entry.detail, entry.diff
    )
    if entry.check != "workflow-presence" or not entry.ok:
        return result
    path = owned_target(root, entry.target)
    if path is None:
        return DriftEntry("ci", entry.target, "unreadable", "workflow-jobs", "workflow target is outside the project")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return DriftEntry("ci", entry.target, "unreadable", "workflow-jobs", "workflow cannot be read as UTF-8")
    workflow = inspect_workflow(text, entry.target)
    return DriftEntry("ci", entry.target, "presence-only" if workflow.ok else "stale", "workflow-jobs", workflow.detail)


def inspect_drift(root: Path) -> DriftReport:
    """Compare recorded regions with current renders and co-owned structural facts."""
    try:
        ownership = inspect_ownership(root)
    except OwnershipPlanTargetError as error:
        raise DriftTargetError(str(error)) from error
    return DriftReport(
        ownership.root,
        ownership.recorded,
        tuple(_drift_entry(ownership.root, entry) for entry in ownership.entries),
        ownership.seeds_excluded,
    )
