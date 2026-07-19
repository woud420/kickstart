"""Data-transfer objects shared across kickstart boundaries."""

from src.model.dto.telemetry import (
    EffectiveTelemetry,
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
    ScaffoldCreateProperties,
    TelemetryDurationBucket,
    TelemetryConsent,
    TelemetryEnvelope,
    TelemetryEvent,
    TelemetryEventName,
    TelemetryIdentityReset,
    TelemetryState,
    TelemetrySuppressionReason,
)

__all__ = [
    "EffectiveTelemetry",
    "ScaffoldCreateErrorCategory",
    "ScaffoldCreateOutcome",
    "ScaffoldCreateProperties",
    "TelemetryConsent",
    "TelemetryDurationBucket",
    "TelemetryEnvelope",
    "TelemetryEvent",
    "TelemetryEventName",
    "TelemetryIdentityReset",
    "TelemetryState",
    "TelemetrySuppressionReason",
]
