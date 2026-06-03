from __future__ import annotations

from src.model.dto import CheckResult, CliConfig


def check(config: CliConfig) -> CheckResult:
    return CheckResult(status="ok", endpoint=config.endpoint)
