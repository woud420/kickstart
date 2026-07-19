"""Data-transfer objects shared across kickstart boundaries."""

from src.model.dto.posthog import PostHogCapturePayload, PostHogCaptureRequest
from src.model.dto.telemetry import (
    EffectiveTelemetry,
    ScaffoldCreateContext,
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
    "PostHogCapturePayload",
    "PostHogCaptureRequest",
    "ScaffoldCreateContext",
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
