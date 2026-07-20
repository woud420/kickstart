from typing import cast
from unittest.mock import Mock, patch

import pytest
import requests

from src.model.dto.posthog import PostHogCapturePayload
from src.telemetry.config import PostHogSettings
from src.telemetry.posthog import PostHogSink, RequestsPostHogTransport
from tests.unit.model.dto.test_posthog_dto import telemetry_envelope


class RecordingTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, PostHogCapturePayload, float]] = []

    def send(self, endpoint: str, payload: PostHogCapturePayload, timeout_seconds: float) -> None:
        self.calls.append((endpoint, payload, timeout_seconds))


class FailingTransport:
    def __init__(self) -> None:
        self.call_count = 0

    def send(self, endpoint: str, payload: PostHogCapturePayload, timeout_seconds: float) -> None:
        self.call_count += 1
        raise requests.Timeout("synthetic timeout")


def test_sink_maps_and_sends_one_request() -> None:
    transport = RecordingTransport()
    settings = PostHogSettings("phc_public_test_token")

    PostHogSink(settings, transport).record(telemetry_envelope())

    assert len(transport.calls) == 1
    endpoint, payload, timeout = transport.calls[0]
    assert endpoint == settings.endpoint
    assert payload["api_key"] == "phc_public_test_token"
    assert timeout == 2.0


def test_sink_does_not_retry_transport_failures() -> None:
    transport = FailingTransport()

    with pytest.raises(requests.Timeout, match="synthetic"):
        PostHogSink(PostHogSettings("phc_public_test_token"), transport).record(telemetry_envelope())

    assert transport.call_count == 1


def test_requests_transport_posts_json_and_checks_response() -> None:
    response = Mock()
    response.status_code = 202
    payload = cast(
        PostHogCapturePayload,
        {
            "api_key": "phc_public_test_token",
            "distinct_id": "anonymous-id",
            "event": "event",
            "timestamp": "now",
            "uuid": "event-id",
            "properties": {},
        },
    )

    with patch("src.telemetry.posthog.requests.post", return_value=response) as post:
        RequestsPostHogTransport().send("https://example.test/capture", payload, 1.5)

    post.assert_called_once_with("https://example.test/capture", json=payload, timeout=1.5, allow_redirects=False)
    response.raise_for_status.assert_called_once_with()


def test_requests_transport_rejects_redirect_without_following_it() -> None:
    response = Mock(status_code=307)
    payload = cast(
        PostHogCapturePayload,
        {
            "api_key": "phc_public_test_token",
            "distinct_id": "anonymous-id",
            "event": "event",
            "timestamp": "now",
            "uuid": "event-id",
            "properties": {},
        },
    )

    with patch("src.telemetry.posthog.requests.post", return_value=response) as post:
        with pytest.raises(requests.HTTPError, match="redirected"):
            RequestsPostHogTransport().send("https://example.test/capture", payload, 1.5)

    post.assert_called_once_with("https://example.test/capture", json=payload, timeout=1.5, allow_redirects=False)
    response.raise_for_status.assert_not_called()
