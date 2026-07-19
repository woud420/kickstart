from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.model.dto.telemetry import (
    CliArtifactKind,
    CliInstallErrorCategory,
    CliInstallOutcome,
    CliInstallProperties,
    CliUpgradeChecksumStatus,
    CliUpgradeErrorCategory,
    CliUpgradeOutcome,
    CliUpgradeProperties,
    ScaffoldCreateContext,
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
    ScaffoldCreateProperties,
    TelemetryDurationBucket,
    TelemetryEvent,
    TelemetryEventName,
    TelemetryEnvelope,
)
from src.model.dto.upgrade import normalize_target_version


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


def test_create_context_cannot_carry_project_name_or_root() -> None:
    assert "name" not in ScaffoldCreateContext.__dataclass_fields__
    assert "root" not in ScaffoldCreateContext.__dataclass_fields__


def test_install_property_mapping_is_an_exact_closed_allowlist() -> None:
    properties = CliInstallProperties(
        cli_version="1.2.3",
        outcome=CliInstallOutcome.SUCCESS,
        error_category=CliInstallErrorCategory.NONE,
        artifact_kind=CliArtifactKind.ONEDIR,
        path_update_requested=True,
        already_on_path=False,
        duration_bucket=TelemetryDurationBucket.ONE_TO_FIVE_SECONDS,
        platform="macos",
        architecture="arm64",
    )

    assert set(properties.as_mapping()) == {
        "already_on_path",
        "architecture",
        "artifact_kind",
        "cli_version",
        "duration_bucket",
        "error_category",
        "outcome",
        "path_update_requested",
        "platform",
    }


def test_upgrade_property_mapping_is_an_exact_closed_allowlist() -> None:
    properties = CliUpgradeProperties(
        cli_version="1.2.3",
        target_version="1.3.0",
        outcome=CliUpgradeOutcome.UPDATED,
        error_category=CliUpgradeErrorCategory.NONE,
        checksum_status=CliUpgradeChecksumStatus.VERIFIED,
        duration_bucket=TelemetryDurationBucket.FIVE_TO_THIRTY_SECONDS,
        platform="linux",
        architecture="x86_64",
    )

    assert set(properties.as_mapping()) == {
        "architecture",
        "checksum_status",
        "cli_version",
        "duration_bucket",
        "error_category",
        "outcome",
        "platform",
        "target_version",
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "unknown"),
        ("v1.2.3", "1.2.3"),
        ("1.2.3", "1.2.3"),
        ("01.2.3", "unknown"),
        ("1.2.3-private", "unknown"),
    ],
)
def test_upgrade_target_version_allows_only_stable_semver(value: str | None, expected: str) -> None:
    assert normalize_target_version(value) == expected
