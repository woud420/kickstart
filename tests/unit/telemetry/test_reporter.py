from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest

from src.model.dto.telemetry import TelemetryConsent, TelemetryEvent
from src.telemetry.posthog import PostHogSink
from src.telemetry.reporter import TelemetryReporter, default_telemetry_reporter
from src.telemetry.sink import InMemoryTelemetrySink, NoOpTelemetrySink
from src.telemetry.state import TelemetryStateStore
from tests.unit.model.dto.test_posthog_dto import telemetry_envelope


EVENT_ID = UUID("33333333-3333-4333-8333-333333333333")
NOW = datetime(2026, 7, 19, 15, 0, tzinfo=UTC)


class FailingSink:
    def record(self, envelope: object) -> None:
        raise RuntimeError("synthetic transport failure")


def _event() -> TelemetryEvent:
    return telemetry_envelope().event


def test_reporter_adds_stable_identity_and_delivery_metadata(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    state = store.enable()
    sink = InMemoryTelemetrySink()
    reporter = TelemetryReporter(
        state_store=store,
        sink=sink,
        environ={},
        development=False,
        clock=lambda: NOW,
        uuid_factory=lambda: EVENT_ID,
    )

    event = _event()
    reporter.record(event)

    assert len(sink.envelopes) == 1
    assert sink.envelopes[0].anonymous_id == state.anonymous_id
    assert sink.envelopes[0].event_id == EVENT_ID
    assert sink.envelopes[0].occurred_at == NOW
    assert sink.envelopes[0].event is event


def test_reporter_creates_and_persists_identity_for_first_default_on_event(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    sink = InMemoryTelemetrySink()
    reporter = TelemetryReporter(
        state_store=store,
        sink=sink,
        environ={},
        development=False,
    )

    reporter.record(_event())

    persisted = store.read()
    assert persisted.consent is TelemetryConsent.ENABLED
    assert persisted.anonymous_id is not None
    assert len(sink.envelopes) == 1
    assert sink.envelopes[0].anonymous_id == persisted.anonymous_id


@pytest.mark.parametrize(
    "environ",
    [
        {"DO_NOT_TRACK": "1"},
        {"KICKSTART_TELEMETRY_DISABLED": "1"},
        {"CI": "1"},
        {"PYTEST_CURRENT_TEST": "test"},
        {"KICKSTART_EVAL": "1"},
    ],
)
def test_hard_suppression_does_not_create_state_or_send(
    tmp_path: Path,
    environ: dict[str, str],
) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    sink = InMemoryTelemetrySink()
    reporter = TelemetryReporter(store, sink, environ, development=False)

    reporter.record(_event())

    assert sink.envelopes == []
    assert not store.path.exists()


def test_explicit_disable_does_not_create_identity_or_send(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    store.disable()
    sink = InMemoryTelemetrySink()

    TelemetryReporter(store, sink, {}, development=False).record(_event())

    assert sink.envelopes == []
    persisted = store.read()
    assert persisted.consent is TelemetryConsent.DISABLED
    assert persisted.anonymous_id is None


def test_disable_between_policy_and_identity_acquisition_wins(tmp_path: Path) -> None:
    class DisableBeforeIdentityStore(TelemetryStateStore):
        def identity_for_event(self) -> UUID | None:
            self.disable()
            return super().identity_for_event()

    store = DisableBeforeIdentityStore(tmp_path / "telemetry.json")
    sink = InMemoryTelemetrySink()

    TelemetryReporter(store, sink, {}, development=False).record(_event())

    assert sink.envelopes == []
    assert store.read().consent is TelemetryConsent.DISABLED


def test_reporter_contains_sink_failures(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    reporter = TelemetryReporter(store, FailingSink(), {}, development=False)

    reporter.record(_event())

    assert store.read().anonymous_id is not None


def test_default_reporter_without_token_uses_noop_sink(tmp_path: Path) -> None:
    reporter = default_telemetry_reporter({"XDG_CONFIG_HOME": str(tmp_path)}, development=False)

    reporter.record(_event())

    assert isinstance(reporter.sink, NoOpTelemetrySink)
    assert not reporter.state_store.path.exists()


def test_environment_token_routes_default_on_event_without_real_network(tmp_path: Path) -> None:
    state_path = tmp_path / "kickstart" / "telemetry.json"
    reporter = default_telemetry_reporter(
        {
            "XDG_CONFIG_HOME": str(tmp_path),
            "POSTHOG_PUBLIC_CUSTOMER_API_TOKEN": "phc_public_test_token",
        },
        development=False,
    )

    with patch.object(PostHogSink, "record") as record:
        reporter.record(_event())

    assert isinstance(reporter.sink, PostHogSink)
    record.assert_called_once()
    assert TelemetryStateStore(state_path).read().anonymous_id is not None


def test_invalid_state_fails_closed_without_sending(tmp_path: Path) -> None:
    state_path = tmp_path / "telemetry.json"
    state_path.write_text("{bad json", encoding="utf-8")
    sink = InMemoryTelemetrySink()

    TelemetryReporter(TelemetryStateStore(state_path), sink, {}, development=False).record(_event())

    assert sink.envelopes == []
    assert state_path.read_text(encoding="utf-8") == "{bad json"


def test_dangling_state_symlink_fails_closed_without_replacement(tmp_path: Path) -> None:
    state_path = tmp_path / "telemetry.json"
    missing_target = tmp_path / "missing-state.json"
    state_path.symlink_to(missing_target)
    sink = InMemoryTelemetrySink()

    TelemetryReporter(TelemetryStateStore(state_path), sink, {}, development=False).record(_event())

    assert sink.envelopes == []
    assert state_path.is_symlink()
    assert not missing_target.exists()
