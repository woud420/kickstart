"""Bounded read-only inspection of the ownership the manifest actually records."""

from dataclasses import dataclass
import json
from pathlib import Path

from src.generator.artifact_checks import has_check_target, owned_target
from src.generator.docs_plan import DocsPlanTargetError, inspect_docs
from src.generator.scaffold_contract import MANIFEST_PATH, ScaffoldContract, load_parsed_manifest
from src.utils.errors import ManifestShapeError, OwnershipPlanTargetError


@dataclass(frozen=True)
class OwnershipEntry:
    target: str
    classification: str
    check: str
    status: str
    detail: str = ""
    diff: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {"in-sync", "presence-only"}


@dataclass(frozen=True)
class OwnershipReport:
    root: Path
    recorded: bool
    entries: tuple[OwnershipEntry, ...] = ()
    seeds_excluded: int = 0

    @property
    def in_sync(self) -> bool:
        return self.recorded and all(entry.ok for entry in self.entries)

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "root": str(self.root),
                    "recorded": self.recorded,
                    "in_sync": self.in_sync,
                    "seeds_excluded": self.seeds_excluded,
                    "detail": "" if self.recorded else "Ownership is unrecorded; current files were not classified.",
                    "entries": [
                        {
                            "target": e.target,
                            "classification": e.classification,
                            "check": e.check,
                            "status": e.status,
                            "detail": e.detail,
                            "diff": e.diff,
                        }
                        for e in self.entries
                    ],
                },
                indent=2,
            )
            + "\n"
        )


def inspect_ownership(root: Path) -> OwnershipReport:
    if not root.is_dir():
        raise OwnershipPlanTargetError(f"ownership plan target '{root}' is not an existing directory")
    resolved = root.resolve()
    manifest_path = owned_target(resolved, MANIFEST_PATH)
    if manifest_path is None:
        raise OwnershipPlanTargetError("manifest target resolves outside the project or cannot be resolved")
    try:
        contract = ScaffoldContract.from_manifest(load_parsed_manifest(manifest_path))
    except ManifestShapeError as error:
        raise OwnershipPlanTargetError(f"cannot inspect persisted ownership: {error}") from error
    if contract.ownership is None:
        return OwnershipReport(resolved, False)
    owned = tuple(record for record in contract.ownership if record.classification != "seed")
    safe = {record.path: owned_target(resolved, record.path) for record in owned}
    selected_ids = frozenset(
        record.artifact_id for record in owned if record.artifact_id is not None and safe[record.path] is not None
    )
    try:
        docs = (
            {entry.target: entry for entry in inspect_docs(resolved, artifact_ids=selected_ids).entries}
            if selected_ids
            else {}
        )
    except DocsPlanTargetError as error:
        raise OwnershipPlanTargetError(str(error)) from error
    entries: list[OwnershipEntry] = []
    for record in owned:
        path = safe[record.path]
        check = record.check or ""
        if path is None:
            entries.append(
                OwnershipEntry(
                    record.path,
                    record.classification,
                    check,
                    "unreadable",
                    "owned target resolves outside the project or cannot be resolved",
                )
            )
        elif record.classification == "managed-region":
            doc = docs[record.path]
            entries.append(OwnershipEntry(record.path, record.classification, check, doc.status, doc.detail, doc.diff))
        else:
            entries.append(_structural_entry(path, record.path, check))
    return OwnershipReport(resolved, True, tuple(entries), len(contract.ownership) - len(owned))


def _structural_entry(path: Path, target: str, check: str) -> OwnershipEntry:
    def entry(status: str, detail: str) -> OwnershipEntry:
        return OwnershipEntry(target, "structural", check, status, detail)

    if not path.is_file():
        return entry("would-create", "recorded structural artifact is missing")
    if check == "manifest-shape":
        return entry("presence-only", "manifest shape validated; bytes are not compared")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return entry("unreadable", str(error))
    if check == "make-check":
        if not has_check_target(text):
            return entry("structural-gap", "no literal check target declaration; Makefile content is not compared")
        return entry("presence-only", "literal check target declared; Makefile content is not compared")
    if not text.strip():
        return entry("structural-gap", "recorded workflow file is empty")
    return entry("presence-only", "workflow file present and readable; job graph and bytes are not compared")
