"""Best-effort telemetry orchestration independent of any event producer."""

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.model.dto.telemetry import TelemetryEnvelope, TelemetryEvent
from src.telemetry.config import posthog_settings_from_configuration
from src.telemetry.policy import resolve_telemetry
from src.telemetry.posthog import PostHogSink
from src.telemetry.sink import NoOpTelemetrySink, TelemetrySink
from src.telemetry.state import TelemetryStateStore


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class TelemetryReporter:
    """Attach consented identity metadata and contain all telemetry failures."""

    state_store: TelemetryStateStore
    sink: TelemetrySink
    environ: Mapping[str, str]
    development: bool | None = None
    clock: Callable[[], datetime] = _utc_now
    uuid_factory: Callable[[], UUID] = uuid4

    def record(self, event: TelemetryEvent) -> None:
        """Attempt one event only when effective policy permits it."""
        try:
            if isinstance(self.sink, NoOpTelemetrySink):
                return
            effective = resolve_telemetry(
                self.state_store,
                self.environ,
                development=self.development,
            )
            if not effective.enabled:
                return
            anonymous_id = self.state_store.identity_for_event()
            if anonymous_id is None:
                return
            envelope = TelemetryEnvelope(
                event_id=self.uuid_factory(),
                anonymous_id=anonymous_id,
                occurred_at=self.clock(),
                event=event,
            )
            self.sink.record(envelope)
        except Exception:
            # Telemetry must never change another command's output or exit status.
            return


def default_telemetry_reporter(
    environ: Mapping[str, str] | None = None,
    *,
    development: bool | None = None,
) -> TelemetryReporter:
    """Build the default reporter without reading cwd configuration or dotenv files."""
    process_environment = os.environ if environ is None else environ
    settings = posthog_settings_from_configuration(process_environment)
    sink: TelemetrySink = NoOpTelemetrySink() if settings is None else PostHogSink(settings)
    return TelemetryReporter(
        state_store=TelemetryStateStore.from_environment(process_environment),
        sink=sink,
        environ=process_environment,
        development=development,
    )
