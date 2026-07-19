from pathlib import Path

import pytest

from src.model.dto.telemetry import TelemetrySuppressionReason
from src.telemetry.policy import resolve_telemetry
from src.telemetry.state import TelemetryStateStore


@pytest.mark.parametrize(
    ("environ", "reason"),
    [
        ({"DO_NOT_TRACK": "1"}, TelemetrySuppressionReason.DO_NOT_TRACK),
        ({"KICKSTART_TELEMETRY_DISABLED": "true"}, TelemetrySuppressionReason.ENVIRONMENT_DISABLED),
        ({"CI": "yes"}, TelemetrySuppressionReason.CI),
        ({"PYTEST_CURRENT_TEST": "test"}, TelemetrySuppressionReason.TEST),
        ({"KICKSTART_EVAL": "on"}, TelemetrySuppressionReason.EVALUATION),
    ],
)
def test_hard_opt_outs_precede_persisted_consent(
    tmp_path: Path,
    environ: dict[str, str],
    reason: TelemetrySuppressionReason,
) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    store.enable()

    resolved = resolve_telemetry(store, environ, development=False)

    assert resolved.enabled is False
    assert resolved.reason is reason
    assert resolved.anonymous_id is None


def test_missing_state_is_disabled_without_creating_an_identity(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")

    resolved = resolve_telemetry(store, {}, development=False)

    assert resolved.enabled is False
    assert resolved.reason is TelemetrySuppressionReason.NOT_OPTED_IN
    assert resolved.anonymous_id is None
    assert not store.path.exists()


def test_enabled_state_is_effective_outside_suppressed_contexts(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    state = store.enable()

    resolved = resolve_telemetry(store, {}, development=False)

    assert resolved.enabled is True
    assert resolved.reason is TelemetrySuppressionReason.ENABLED
    assert resolved.anonymous_id == state.anonymous_id


def test_source_checkout_is_disabled_without_explicit_development_override(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    store.enable()

    disabled = resolve_telemetry(store, {}, development=True)
    enabled = resolve_telemetry(
        store,
        {"KICKSTART_TELEMETRY_ALLOW_DEVELOPMENT": "1"},
        development=True,
    )

    assert disabled.reason is TelemetrySuppressionReason.DEVELOPMENT
    assert enabled.enabled is True


def test_malformed_state_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.json"
    path.write_text("{bad json", encoding="utf-8")

    resolved = resolve_telemetry(TelemetryStateStore(path), {}, development=False)

    assert resolved.enabled is False
    assert resolved.reason is TelemetrySuppressionReason.INVALID_STATE
