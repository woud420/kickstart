"""Typed, provider-neutral results for the self-upgrade workflow."""

import re
from dataclasses import dataclass

from src.model.dto.telemetry import (
    CliUpgradeChecksumStatus,
    CliUpgradeErrorCategory,
    CliUpgradeOutcome,
)


_STABLE_SEMVER = re.compile(r"^v?((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))$")
UNKNOWN_TARGET_VERSION = "unknown"


def normalize_target_version(value: str | None) -> str:
    """Return a stable semantic version without a leading ``v``, or ``unknown``."""
    if value is None:
        return UNKNOWN_TARGET_VERSION
    match = _STABLE_SEMVER.fullmatch(value)
    return match.group(1) if match is not None else UNKNOWN_TARGET_VERSION


@dataclass(frozen=True)
class UpgradeResult:
    """Safe terminal result returned by the updater to its CLI caller."""

    target_version: str
    outcome: CliUpgradeOutcome
    error_category: CliUpgradeErrorCategory
    checksum_status: CliUpgradeChecksumStatus
