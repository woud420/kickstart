"""PostHog-specific wire DTOs for the replaceable telemetry adapter."""

from dataclasses import dataclass, field
from datetime import UTC
from typing import TypedDict

from src.model.dto.telemetry import TelemetryEnvelope, TelemetryPropertyValue


class PostHogCapturePayload(TypedDict):
    """The exact JSON object accepted by PostHog's single-event endpoint."""

    api_key: str
    event: str
    distinct_id: str
    timestamp: str
    uuid: str
    properties: dict[str, TelemetryPropertyValue]


@dataclass(frozen=True)
class PostHogCaptureRequest:
    """Map one provider-neutral envelope to PostHog without expanding its data."""

    project_token: str = field(repr=False)
    envelope: TelemetryEnvelope

    def __post_init__(self) -> None:
        if not self.project_token.startswith("phc_") or len(self.project_token) == len("phc_"):
            raise ValueError("PostHog capture requires a public phc_ project token")

    def as_payload(self) -> PostHogCapturePayload:
        """Return a new exact payload containing only approved and reserved fields."""
        occurred_at = self.envelope.occurred_at
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("Telemetry timestamps must be timezone-aware")
        properties = self.envelope.event.properties.as_mapping()
        properties["$process_person_profile"] = False
        timestamp = occurred_at.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        return {
            "api_key": self.project_token,
            "distinct_id": str(self.envelope.anonymous_id),
            "event": self.envelope.event.name.value,
            "timestamp": timestamp,
            "uuid": str(self.envelope.event_id),
            "properties": properties,
        }
