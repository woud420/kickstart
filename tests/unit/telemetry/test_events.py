from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.model.dto.telemetry import (
    CliArtifactKind,
    CliInstallErrorCategory,
    CliInstallOutcome,
    CliUpgradeChecksumStatus,
    CliUpgradeErrorCategory,
    CliUpgradeOutcome,
    ScaffoldCreateContext,
    ScaffoldCreateErrorCategory,
    ScaffoldCreateOutcome,
    TelemetryDurationBucket,
)
from src.model.dto.upgrade import UpgradeResult
from src.telemetry.events import (
    build_cli_install_event,
    build_cli_upgrade_event,
    build_scaffold_create_event,
    capture_cli_install_terminal,
    capture_cli_upgrade_terminal,
    capture_scaffold_create_terminal,
    classify_cli_install_exception,
    classify_scaffold_create_exception,
)
from src.telemetry.reporter import TelemetryReporter
from src.telemetry.sink import InMemoryTelemetrySink
from src.telemetry.state import TelemetryStateStore
from src.utils.errors import (
    ExtensionError,
    KickstartError,
    ProjectCreationError,
    UnsupportedOptionError,
    UnsupportedProjectTypeError,
)


def _service_context() -> ScaffoldCreateContext:
    return ScaffoldCreateContext(
        project_type="service",
        language="ts",
        runtime="docker",
        cloud="private-cloud-value",
        framework=None,
        database="POSTGRES",
        cache="redis",
        auth="jwt",
        knowledge="private-knowledge-value",
        workspace_tooling="private-workspace-value",
        helm=True,
        github_requested=True,
        interactive=False,
    )


def test_install_event_contains_only_normalized_closed_properties() -> None:
    event = build_cli_install_event(
        CliInstallOutcome.SUCCESS,
        CliInstallErrorCategory.NONE,
        CliArtifactKind.SINGLE_FILE,
        path_update_requested=False,
        already_on_path=True,
        duration_seconds=0.5,
        cli_version="1.2.3",
        platform_name="Darwin",
        architecture="aarch64",
    )

    assert event.name.value == "cli_install_completed"
    assert event.properties.as_mapping() == {
        "already_on_path": True,
        "architecture": "arm64",
        "artifact_kind": "single_file",
        "cli_version": "1.2.3",
        "duration_bucket": "under_1s",
        "error_category": "none",
        "outcome": "success",
        "path_update_requested": False,
        "platform": "macos",
    }


def test_upgrade_event_replaces_non_stable_target_version_with_unknown() -> None:
    result = UpgradeResult(
        target_version="v1.2.3-private-value",
        outcome=CliUpgradeOutcome.FAILED,
        error_category=CliUpgradeErrorCategory.ARCHIVE_MISSING,
        checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
    )

    event = build_cli_upgrade_event(
        result,
        6,
        cli_version="1.2.2",
        platform_name="Linux",
        architecture="amd64",
    )

    assert event.name.value == "cli_upgrade_completed"
    assert event.properties.as_mapping() == {
        "architecture": "x86_64",
        "checksum_status": "not_reached",
        "cli_version": "1.2.2",
        "duration_bucket": "5_to_30s",
        "error_category": "archive_missing",
        "outcome": "failed",
        "platform": "linux",
        "target_version": "unknown",
    }


@pytest.mark.parametrize(
    ("error", "during_path_update", "expected"),
    [
        (RuntimeError("private detail"), True, CliInstallErrorCategory.PATH_UPDATE),
        (FileNotFoundError("private detail"), False, CliInstallErrorCategory.SOURCE_MISSING),
        (FileExistsError("private detail"), False, CliInstallErrorCategory.DESTINATION_CONFLICT),
        (PermissionError("private detail"), False, CliInstallErrorCategory.PERMISSION_DENIED),
        (OSError("private detail"), False, CliInstallErrorCategory.FILESYSTEM_ERROR),
        (KickstartError("private detail"), False, CliInstallErrorCategory.EXPECTED_ERROR),
        (RuntimeError("private detail"), False, CliInstallErrorCategory.UNEXPECTED_ERROR),
    ],
)
def test_install_exception_classification_never_uses_exception_text(
    error: Exception,
    during_path_update: bool,
    expected: CliInstallErrorCategory,
) -> None:
    assert classify_cli_install_exception(error, during_path_update=during_path_update) is expected


def test_lifecycle_capture_helpers_record_through_the_shared_reporter(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    sink = InMemoryTelemetrySink()
    reporter = TelemetryReporter(store, sink, {}, development=False)
    upgrade = UpgradeResult(
        target_version="1.2.3",
        outcome=CliUpgradeOutcome.UPDATED,
        error_category=CliUpgradeErrorCategory.NONE,
        checksum_status=CliUpgradeChecksumStatus.VERIFIED,
    )

    capture_cli_install_terminal(
        CliInstallOutcome.SUCCESS,
        CliInstallErrorCategory.NONE,
        CliArtifactKind.ONEDIR,
        path_update_requested=True,
        already_on_path=False,
        duration_seconds=1,
        cli_version="1.2.2",
        reporter=reporter,
    )
    capture_cli_upgrade_terminal(
        upgrade,
        2,
        cli_version="1.2.2",
        reporter=reporter,
    )

    assert [envelope.event.name.value for envelope in sink.envelopes] == [
        "cli_install_completed",
        "cli_upgrade_completed",
    ]
    assert sink.envelopes[0].anonymous_id == sink.envelopes[1].anonymous_id


@pytest.mark.parametrize("capture", ["install", "upgrade"])
def test_lifecycle_capture_helpers_contain_reporter_failures(capture: str) -> None:
    reporter = Mock(spec=TelemetryReporter)
    reporter.record.side_effect = RuntimeError("synthetic reporter failure")

    if capture == "install":
        capture_cli_install_terminal(
            CliInstallOutcome.FAILED,
            CliInstallErrorCategory.UNEXPECTED_ERROR,
            CliArtifactKind.UNKNOWN,
            path_update_requested=False,
            already_on_path=False,
            duration_seconds=0,
            cli_version="1.2.3",
            reporter=reporter,
        )
    else:
        capture_cli_upgrade_terminal(
            UpgradeResult(
                target_version="unknown",
                outcome=CliUpgradeOutcome.FAILED,
                error_category=CliUpgradeErrorCategory.UNEXPECTED_ERROR,
                checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
            ),
            0,
            cli_version="1.2.3",
            reporter=reporter,
        )

    reporter.record.assert_called_once()


def test_service_event_canonicalizes_aliases_and_ignores_inapplicable_values() -> None:
    event = build_scaffold_create_event(
        _service_context(),
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        2.5,
        cli_version="0.4.3",
        platform_name="Darwin",
        architecture="aarch64",
    )

    assert event.properties.as_mapping() == {
        "architecture": "arm64",
        "auth": "jwt",
        "cache": "redis",
        "cli_version": "0.4.3",
        "cloud": "none",
        "database": "postgres",
        "duration_bucket": "1_to_5s",
        "error_category": "none",
        "framework": "none",
        "github_requested": True,
        "helm": True,
        "interactive": False,
        "knowledge": "none",
        "language": "typescript",
        "outcome": "success",
        "platform": "macos",
        "project_type": "service",
        "runtime": "container",
        "workspace_tooling": "none",
    }


@pytest.mark.parametrize(
    ("framework", "expected"),
    [(" FASTAPI ", "fastapi"), ("private-framework", "unknown")],
)
def test_service_framework_is_normalized_without_exposing_raw_values(framework: str, expected: str) -> None:
    context = replace(_service_context(), language="python", framework=framework)

    mapping = build_scaffold_create_event(
        context,
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        0.25,
        cli_version="0.4.3",
        platform_name="Linux",
        architecture="x86_64",
    ).properties.as_mapping()

    assert mapping["framework"] == expected
    assert framework not in mapping.values()


def test_legacy_monorepo_event_uses_system_defaults() -> None:
    context = ScaffoldCreateContext(
        project_type="monorepo",
        language="private-language-value",
        runtime="k8s",
        cloud="google",
        framework="private-framework-value",
        database="private-database-value",
        cache="private-cache-value",
        auth="private-auth-value",
        knowledge="both",
        workspace_tooling=None,
        helm=False,
        github_requested=False,
        interactive=True,
    )

    properties = build_scaffold_create_event(
        context,
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        10,
        cli_version="0.4.3",
        platform_name="Linux",
        architecture="amd64",
    ).properties

    assert properties.project_type == "system"
    assert properties.language == "none"
    assert properties.runtime == "kubernetes"
    assert properties.cloud == "gcp"
    assert properties.knowledge == "both"
    assert properties.workspace_tooling == "bun-turbo"
    assert properties.framework == "none"
    assert properties.database == "none"
    assert properties.duration_bucket is TelemetryDurationBucket.FIVE_TO_THIRTY_SECONDS


def test_canonical_system_defaults_to_vendor_neutral_workspace() -> None:
    context = ScaffoldCreateContext(
        project_type="system",
        language="python",
        runtime=None,
        cloud="multi",
        framework=None,
        database=None,
        cache=None,
        auth=None,
        knowledge="none",
        workspace_tooling=None,
        helm=False,
        github_requested=False,
        interactive=False,
    )

    properties = build_scaffold_create_event(
        context,
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        0.5,
        cli_version="0.4.3",
        platform_name="Windows",
        architecture="unknown-cpu",
    ).properties

    assert properties.workspace_tooling == "none"
    assert properties.runtime == "kubernetes"
    assert properties.platform == "windows"
    assert properties.architecture == "other"


def test_unknown_inputs_are_reduced_to_fixed_values_without_raw_data() -> None:
    raw_values = {
        "private-project-type",
        "private-language",
        "private-runtime",
        "private-cloud",
        "private-framework",
        "private-database",
        "private-cache",
        "private-auth",
        "private-knowledge",
        "private-workspace",
    }
    context = ScaffoldCreateContext(
        project_type="private-project-type",
        language="private-language",
        runtime="private-runtime",
        cloud="private-cloud",
        framework="private-framework",
        database="private-database",
        cache="private-cache",
        auth="private-auth",
        knowledge="private-knowledge",
        workspace_tooling="private-workspace",
        helm=False,
        github_requested=False,
        interactive=False,
    )

    mapping = build_scaffold_create_event(
        context,
        ScaffoldCreateOutcome.INVALID_CONFIGURATION,
        ScaffoldCreateErrorCategory.INVALID_CONFIGURATION,
        30,
        cli_version="0.4.3",
        platform_name="private-platform",
        architecture="private-architecture",
    ).properties.as_mapping()

    assert mapping["project_type"] == "unknown"
    assert mapping["language"] == "unknown"
    assert mapping["platform"] == "other"
    assert mapping["architecture"] == "other"
    assert raw_values.isdisjoint(set(str(value) for value in mapping.values()))
    assert {"name", "root", "path", "error", "exception"}.isdisjoint(mapping)


@pytest.mark.parametrize(
    ("error", "outcome", "category"),
    [
        (
            UnsupportedProjectTypeError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.UNSUPPORTED_PROJECT_TYPE,
        ),
        (
            UnsupportedOptionError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.UNSUPPORTED_OPTION,
        ),
        (
            ExtensionError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.INVALID_CONFIGURATION,
        ),
        (
            ProjectCreationError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.PROJECT_CREATION_ERROR,
        ),
        (
            KickstartError("private detail"),
            ScaffoldCreateOutcome.EXPECTED_ERROR,
            ScaffoldCreateErrorCategory.EXPECTED_ERROR,
        ),
        (
            ValueError("private detail"),
            ScaffoldCreateOutcome.INVALID_CONFIGURATION,
            ScaffoldCreateErrorCategory.INVALID_CONFIGURATION,
        ),
        (
            RuntimeError("private detail"),
            ScaffoldCreateOutcome.UNEXPECTED_ERROR,
            ScaffoldCreateErrorCategory.UNEXPECTED_ERROR,
        ),
    ],
)
def test_exception_classification_never_uses_exception_text(
    error: Exception,
    outcome: ScaffoldCreateOutcome,
    category: ScaffoldCreateErrorCategory,
) -> None:
    assert classify_scaffold_create_exception(error) == (outcome, category)


@pytest.mark.parametrize(
    ("duration", "bucket"),
    [
        (0.999, TelemetryDurationBucket.UNDER_ONE_SECOND),
        (1.0, TelemetryDurationBucket.ONE_TO_FIVE_SECONDS),
        (5.0, TelemetryDurationBucket.FIVE_TO_THIRTY_SECONDS),
        (30.0, TelemetryDurationBucket.THIRTY_SECONDS_OR_MORE),
    ],
)
def test_duration_boundaries_use_coarse_buckets(duration: float, bucket: TelemetryDurationBucket) -> None:
    event = build_scaffold_create_event(
        _service_context(),
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        duration,
        cli_version="0.4.3",
        platform_name="Linux",
        architecture="x86_64",
    )

    assert event.properties.duration_bucket is bucket


def test_capture_helper_records_exactly_one_event_for_enabled_reporter(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    store.enable()
    sink = InMemoryTelemetrySink()
    reporter = TelemetryReporter(store, sink, {}, development=False)

    capture_scaffold_create_terminal(
        _service_context(),
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        0.25,
        cli_version="0.4.3",
        reporter=reporter,
    )

    assert len(sink.envelopes) == 1
    assert sink.envelopes[0].event.properties.outcome is ScaffoldCreateOutcome.SUCCESS


def test_capture_helper_contains_unexpected_reporter_failures() -> None:
    reporter = Mock(spec=TelemetryReporter)
    reporter.record.side_effect = RuntimeError("synthetic reporter failure")

    capture_scaffold_create_terminal(
        _service_context(),
        ScaffoldCreateOutcome.SUCCESS,
        ScaffoldCreateErrorCategory.NONE,
        0.25,
        cli_version="0.4.3",
        reporter=reporter,
    )

    reporter.record.assert_called_once()
