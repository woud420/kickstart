"""Fail-closed telemetry enablement policy."""

import os
from collections.abc import Mapping
from pathlib import Path

from src.model.dto.telemetry import EffectiveTelemetry, TelemetryConsent, TelemetryState, TelemetrySuppressionReason
from src.telemetry.state import TelemetryStateStore
from src.utils.errors import TelemetryStateError


_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def resolve_telemetry(
    store: TelemetryStateStore,
    environ: Mapping[str, str] | None = None,
    *,
    development: bool | None = None,
    state: TelemetryState | None = None,
) -> EffectiveTelemetry:
    """Resolve hard opt-outs before consulting persisted consent."""
    process_environment = os.environ if environ is None else environ
    if _truthy(process_environment.get("DO_NOT_TRACK")):
        return _disabled(TelemetrySuppressionReason.DO_NOT_TRACK)
    if _truthy(process_environment.get("KICKSTART_TELEMETRY_DISABLED")):
        return _disabled(TelemetrySuppressionReason.ENVIRONMENT_DISABLED)
    if _truthy(process_environment.get("CI")):
        return _disabled(TelemetrySuppressionReason.CI)
    if "PYTEST_CURRENT_TEST" in process_environment:
        return _disabled(TelemetrySuppressionReason.TEST)
    if _truthy(process_environment.get("KICKSTART_EVAL")):
        return _disabled(TelemetrySuppressionReason.EVALUATION)

    development_run = _is_source_checkout() if development is None else development
    if development_run and not _truthy(process_environment.get("KICKSTART_TELEMETRY_ALLOW_DEVELOPMENT")):
        return _disabled(TelemetrySuppressionReason.DEVELOPMENT)

    try:
        current_state = store.read() if state is None else state
    except TelemetryStateError:
        return _disabled(TelemetrySuppressionReason.INVALID_STATE)
    if current_state.consent is TelemetryConsent.ENABLED and current_state.anonymous_id is not None:
        return EffectiveTelemetry(
            enabled=True,
            reason=TelemetrySuppressionReason.ENABLED,
            anonymous_id=current_state.anonymous_id,
        )
    reason = (
        TelemetrySuppressionReason.USER_DISABLED
        if current_state.consent is TelemetryConsent.DISABLED
        else TelemetrySuppressionReason.NOT_OPTED_IN
    )
    return EffectiveTelemetry(enabled=False, reason=reason, anonymous_id=current_state.anonymous_id)


def _disabled(reason: TelemetrySuppressionReason) -> EffectiveTelemetry:
    return EffectiveTelemetry(enabled=False, reason=reason, anonymous_id=None)


def _truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in _TRUTHY_VALUES


def _is_source_checkout() -> bool:
    repository_root = Path(__file__).resolve().parents[2]
    return (repository_root / ".git").exists() and (repository_root / "pyproject.toml").exists()
