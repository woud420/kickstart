from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.model.dto.posthog import PostHogCaptureRequest
from src.model.dto.telemetry import (
    CliArtifactKind,
    CliInstallErrorCategory,
    CliInstallOutcome,
    CliInstallProperties,
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
    ScaffoldCreateProperties,
    TelemetryDurationBucket,
    TelemetryEnvelope,
    TelemetryEvent,
    TelemetryEventName,
)


EVENT_ID = UUID("11111111-1111-4111-8111-111111111111")
ANONYMOUS_ID = UUID("22222222-2222-4222-8222-222222222222")
OCCURRED_AT = datetime(2026, 7, 19, 14, 30, 15, 123456, tzinfo=UTC)


def telemetry_envelope() -> TelemetryEnvelope:
    return TelemetryEnvelope(
        event_id=EVENT_ID,
        anonymous_id=ANONYMOUS_ID,
        occurred_at=OCCURRED_AT,
        event=TelemetryEvent(
            name=TelemetryEventName.SCAFFOLD_CREATE_COMPLETED,
            properties=ScaffoldCreateProperties(
                cli_version="0.4.3",
                project_type="service",
                language="python",
                runtime="container",
                cloud="none",
                framework="fastapi",
                database="postgres",
                cache="redis",
                auth="none",
                knowledge="none",
                workspace_tooling="none",
                helm=False,
                github_requested=True,
                interactive=False,
                outcome=ScaffoldCreateOutcome.SUCCESS,
                error_category=ScaffoldCreateErrorCategory.NONE,
                duration_bucket=TelemetryDurationBucket.ONE_TO_FIVE_SECONDS,
                platform="linux",
                architecture="x86_64",
            ),
        ),
    )


def test_request_maps_only_allowlisted_and_required_posthog_fields() -> None:
    request = PostHogCaptureRequest(project_token="phc_public_test_token", envelope=telemetry_envelope())

    assert request.as_payload() == {
        "api_key": "phc_public_test_token",
        "distinct_id": str(ANONYMOUS_ID),
        "event": "scaffold_create_completed",
        "timestamp": "2026-07-19T14:30:15.123Z",
        "uuid": str(EVENT_ID),
        "properties": {
            "$process_person_profile": False,
            "architecture": "x86_64",
            "auth": "none",
            "cache": "redis",
            "cli_version": "0.4.3",
            "cloud": "none",
            "database": "postgres",
            "duration_bucket": "1_to_5s",
            "error_category": "none",
            "framework": "fastapi",
            "github_requested": True,
            "helm": False,
            "interactive": False,
            "knowledge": "none",
            "language": "python",
            "outcome": "success",
            "platform": "linux",
            "project_type": "service",
            "runtime": "container",
            "workspace_tooling": "none",
        },
    }


def test_request_maps_lifecycle_events_through_the_same_provider_boundary() -> None:
    envelope = TelemetryEnvelope(
        event_id=EVENT_ID,
        anonymous_id=ANONYMOUS_ID,
        occurred_at=OCCURRED_AT,
        event=TelemetryEvent(
            name=TelemetryEventName.CLI_INSTALL_COMPLETED,
            properties=CliInstallProperties(
                cli_version="1.2.3",
                outcome=CliInstallOutcome.SUCCESS,
                error_category=CliInstallErrorCategory.NONE,
                artifact_kind=CliArtifactKind.ONEDIR,
                path_update_requested=True,
                already_on_path=False,
                duration_bucket=TelemetryDurationBucket.ONE_TO_FIVE_SECONDS,
                platform="macos",
                architecture="arm64",
            ),
        ),
    )

    payload = PostHogCaptureRequest("phc_public_test_token", envelope).as_payload()

    assert payload["event"] == "cli_install_completed"
    assert payload["properties"] == {
        "$process_person_profile": False,
        "already_on_path": False,
        "architecture": "arm64",
        "artifact_kind": "onedir",
        "cli_version": "1.2.3",
        "duration_bucket": "1_to_5s",
        "error_category": "none",
        "outcome": "success",
        "path_update_requested": True,
        "platform": "macos",
    }


def test_request_repr_never_contains_project_token() -> None:
    request = PostHogCaptureRequest(project_token="phc_do_not_print", envelope=telemetry_envelope())

    assert "phc_do_not_print" not in repr(request)


def test_request_rejects_non_public_token() -> None:
    with pytest.raises(ValueError, match="public phc_"):
        PostHogCaptureRequest(project_token="phx_personal_key", envelope=telemetry_envelope())


def test_request_rejects_empty_public_token_body() -> None:
    with pytest.raises(ValueError, match="public phc_"):
        PostHogCaptureRequest(project_token="phc_", envelope=telemetry_envelope())


def test_request_rejects_naive_timestamp() -> None:
    envelope = telemetry_envelope()
    naive_envelope = TelemetryEnvelope(
        event_id=envelope.event_id,
        anonymous_id=envelope.anonymous_id,
        occurred_at=datetime(2026, 7, 19, 14, 30),
        event=envelope.event,
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        PostHogCaptureRequest("phc_public_test_token", naive_envelope).as_payload()
