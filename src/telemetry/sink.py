"""Provider-neutral telemetry sink interfaces."""

from dataclasses import dataclass, field
from typing import Protocol

from src.model.dto.telemetry import TelemetryEnvelope


class TelemetrySink(Protocol):
    """A replaceable destination for a fully formed telemetry envelope."""

    def record(self, envelope: TelemetryEnvelope) -> None:
        """Record an envelope or raise a transport-specific exception."""


class NoOpTelemetrySink:
    """Discard telemetry without side effects."""

    def record(self, envelope: TelemetryEnvelope) -> None:
        """Intentionally discard the envelope."""


@dataclass
class InMemoryTelemetrySink:
    """Record exact envelopes for tests without network access."""

    envelopes: list[TelemetryEnvelope] = field(default_factory=list)

    def record(self, envelope: TelemetryEnvelope) -> None:
        """Append one envelope to the in-memory record."""
        self.envelopes.append(envelope)
