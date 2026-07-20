"""PostHog transport adapter for provider-neutral telemetry envelopes."""

from dataclasses import dataclass, field
from typing import Protocol

import requests

from src.model.dto.posthog import PostHogCapturePayload, PostHogCaptureRequest
from src.model.dto.telemetry import TelemetryEnvelope
from src.telemetry.config import PostHogSettings


class PostHogTransport(Protocol):
    """Minimal injectable HTTP boundary used by the PostHog sink."""

    def send(self, endpoint: str, payload: PostHogCapturePayload, timeout_seconds: float) -> None:
        """Send one payload or raise a transport-specific exception."""


class RequestsPostHogTransport:
    """Issue exactly one blocking HTTP request with no transport retries."""

    def send(self, endpoint: str, payload: PostHogCapturePayload, timeout_seconds: float) -> None:
        response = requests.post(endpoint, json=payload, timeout=timeout_seconds, allow_redirects=False)
        if 300 <= response.status_code < 400:
            raise requests.HTTPError("PostHog capture endpoint redirected", response=response)
        response.raise_for_status()


@dataclass(frozen=True)
class PostHogSink:
    """Map and deliver envelopes through the replaceable sink interface."""

    settings: PostHogSettings
    transport: PostHogTransport = field(default_factory=RequestsPostHogTransport)

    def record(self, envelope: TelemetryEnvelope) -> None:
        request = PostHogCaptureRequest(project_token=self.settings.project_token, envelope=envelope)
        self.transport.send(self.settings.endpoint, request.as_payload(), self.settings.timeout_seconds)
