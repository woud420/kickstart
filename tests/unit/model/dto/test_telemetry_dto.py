from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.model.dto.telemetry import (
    TelemetryEnvelope,
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
    ScaffoldCreateProperties,
    TelemetryDurationBucket,
    TelemetryEvent,
    TelemetryEventName,
)


def _properties() -> ScaffoldCreateProperties:
    return ScaffoldCreateProperties(
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
    )


def test_event_properties_use_a_frozen_closed_dto() -> None:
    properties = _properties()
    event = TelemetryEvent(TelemetryEventName.SCAFFOLD_CREATE_COMPLETED, properties)

    assert event.properties.project_type == "service"
    with pytest.raises(FrozenInstanceError):
        setattr(event.properties, "project_type", "frontend")


def test_property_mapping_contains_only_the_documented_allowlist() -> None:
    assert set(_properties().as_mapping()) == {
        "architecture",
        "auth",
        "cache",
        "cli_version",
        "cloud",
        "database",
        "duration_bucket",
        "error_category",
        "framework",
        "github_requested",
        "helm",
        "interactive",
        "knowledge",
        "language",
        "outcome",
        "platform",
        "project_type",
        "runtime",
        "workspace_tooling",
    }


def test_envelope_uses_provider_neutral_identity_names() -> None:
    envelope = TelemetryEnvelope(
        event_id=uuid4(),
        anonymous_id=uuid4(),
        occurred_at=datetime.now(UTC),
        event=TelemetryEvent(TelemetryEventName.SCAFFOLD_CREATE_COMPLETED, _properties()),
    )

    assert "posthog" not in repr(envelope).lower()
    assert envelope.anonymous_id.version == 4
