from datetime import UTC, datetime
from uuid import uuid4

from src.model.dto.telemetry import (
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
    ScaffoldCreateProperties,
    TelemetryDurationBucket,
    TelemetryEnvelope,
    TelemetryEvent,
    TelemetryEventName,
)
from src.telemetry.sink import InMemoryTelemetrySink, NoOpTelemetrySink


def _envelope() -> TelemetryEnvelope:
    return TelemetryEnvelope(
        event_id=uuid4(),
        anonymous_id=uuid4(),
        occurred_at=datetime.now(UTC),
        event=TelemetryEvent(
            TelemetryEventName.SCAFFOLD_CREATE_COMPLETED,
            ScaffoldCreateProperties(
                cli_version="0.4.3",
                project_type="service",
                language="python",
                runtime="container",
                cloud="none",
                framework="fastapi",
                database="none",
                cache="none",
                auth="none",
                knowledge="none",
                workspace_tooling="none",
                helm=False,
                github_requested=False,
                interactive=False,
                outcome=ScaffoldCreateOutcome.SUCCESS,
                error_category=ScaffoldCreateErrorCategory.NONE,
                duration_bucket=TelemetryDurationBucket.UNDER_ONE_SECOND,
                platform="linux",
                architecture="x86_64",
            ),
        ),
    )


def test_noop_sink_discards_without_error() -> None:
    NoOpTelemetrySink().record(_envelope())


def test_in_memory_sink_records_exact_envelope() -> None:
    sink = InMemoryTelemetrySink()
    envelope = _envelope()

    sink.record(envelope)

    assert sink.envelopes == [envelope]
