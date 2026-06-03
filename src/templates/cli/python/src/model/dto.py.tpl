from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CliConfig:
    endpoint: str


@dataclass(frozen=True)
class CheckResult:
    status: str
    endpoint: str
