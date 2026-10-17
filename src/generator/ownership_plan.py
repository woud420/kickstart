"""Typed ownership plans derived from generator write targets, never current files."""

from collections.abc import Collection
from dataclasses import dataclass
import re
from typing import cast

from src.generator.managed_artifacts import ALL_MANAGED_DOCS, WORKFLOW_PATTERN
from src.generator.manifest_types import (
    MANIFEST_PATH,
    OwnershipCheck,
    OwnershipClass,
    OwnershipManifest,
    OwnershipTag,
)


@dataclass(frozen=True)
class OwnershipRecord:
    path: str
    classification: OwnershipClass
    artifact_id: str | None = None
    check: OwnershipCheck | None = None

    def manifest(self) -> OwnershipTag:
        if self.classification == "seed":
            return "seed"
        if self.classification == "managed-region":
            assert self.artifact_id is not None
            return cast(OwnershipTag, self.artifact_id)
        assert self.check is not None
        return cast(OwnershipTag, self.check)


def plan_generated_ownership(paths: Collection[str]) -> tuple[OwnershipRecord, ...]:
    managed = {artifact.target: artifact for artifact in ALL_MANAGED_DOCS}
    records: list[OwnershipRecord] = []
    for path in sorted(set(paths)):
        if path in managed:
            artifact = managed[path]
            check: OwnershipCheck = "fenced-content" if artifact.comparison == "content" else "fenced-presence"
            records.append(OwnershipRecord(path, "managed-region", artifact.id, check))
        elif path == "Makefile":
            records.append(OwnershipRecord(path, "structural", check="make-check"))
        elif path == MANIFEST_PATH:
            records.append(OwnershipRecord(path, "structural", check="manifest-shape"))
        elif re.fullmatch(WORKFLOW_PATTERN, path):
            records.append(OwnershipRecord(path, "structural", check="workflow-presence"))
        else:
            records.append(OwnershipRecord(path, "seed"))
    return tuple(records)


def ownership_from_manifest(value: OwnershipManifest | None) -> tuple[OwnershipRecord, ...] | None:
    if value is None:
        return None
    managed = {artifact.id: artifact for artifact in ALL_MANAGED_DOCS}
    records: list[OwnershipRecord] = []
    for path, tag in sorted(value.items()):
        if tag == "seed":
            records.append(OwnershipRecord(path, "seed"))
        elif tag in managed:
            artifact = managed[tag]
            check: OwnershipCheck = "fenced-content" if artifact.comparison == "content" else "fenced-presence"
            records.append(OwnershipRecord(path, "managed-region", tag, check))
        else:
            records.append(OwnershipRecord(path, "structural", check=cast(OwnershipCheck, tag)))
    return tuple(records)
