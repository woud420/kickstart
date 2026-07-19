from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from src.model.dto.telemetry import TelemetryEvent
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


def test_reporter_does_nothing_before_opt_in(tmp_path: Path) -> None:
    sink = InMemoryTelemetrySink()
    reporter = TelemetryReporter(
        state_store=TelemetryStateStore(tmp_path / "telemetry.json"),
        sink=sink,
        environ={},
        development=False,
    )

    reporter.record(_event())

    assert sink.envelopes == []


def test_reporter_contains_sink_failures(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    store.enable()
    reporter = TelemetryReporter(store, FailingSink(), {}, development=False)

    reporter.record(_event())


def test_default_reporter_without_token_uses_noop_sink(tmp_path: Path) -> None:
    reporter = default_telemetry_reporter({"XDG_CONFIG_HOME": str(tmp_path)}, development=False)
    reporter.state_store.enable()

    reporter.record(_event())

    assert isinstance(reporter.sink, NoOpTelemetrySink)


def test_environment_token_does_not_enable_telemetry(tmp_path: Path) -> None:
    state_path = tmp_path / "kickstart" / "telemetry.json"
    reporter = default_telemetry_reporter(
        {
            "XDG_CONFIG_HOME": str(tmp_path),
            "POSTHOG_PUBLIC_CUSTOMER_API_TOKEN": "phc_public_test_token",
        },
        development=False,
    )

    reporter.record(_event())

    assert isinstance(reporter.sink, PostHogSink)
    assert not state_path.exists()
