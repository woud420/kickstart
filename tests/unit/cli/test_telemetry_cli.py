import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli.main import app
from src.telemetry.state import TelemetryStateStore
from src.utils.errors import TelemetryStateError


def _env(tmp_path: Path) -> dict[str, str]:
    return {
        "CI": "0",
        "HOME": str(tmp_path),
        "KICKSTART_TELEMETRY_ALLOW_DEVELOPMENT": "1",
        "POSTHOG_PUBLIC_CUSTOMER_API_TOKEN": "",
        "XDG_CONFIG_HOME": str(tmp_path),
    }


def test_status_is_read_only_for_default_enabled_missing_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    runner = CliRunner()

    result = runner.invoke(app, ["telemetry", "status", "--json"], env=_env(tmp_path))

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["consent"] == "unset"
    assert payload["delivery_configured"] is False
    assert payload["effective"] is True
    assert payload["reason"] == "default_enabled"
    assert payload["anonymous_id"] is None
    assert not (tmp_path / "kickstart" / "telemetry.json").exists()


def test_status_reports_runtime_delivery_configuration_without_exposing_token(tmp_path: Path) -> None:
    environment = _env(tmp_path)
    environment["POSTHOG_PUBLIC_CUSTOMER_API_TOKEN"] = "phc_status_test_token"

    result = CliRunner().invoke(app, ["telemetry", "status", "--json"], env=environment)

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["delivery_configured"] is True
    assert "phc_status_test_token" not in result.stdout
    assert not (tmp_path / "kickstart" / "telemetry.json").exists()


def test_status_supports_human_readable_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = CliRunner().invoke(app, ["telemetry", "status"], env=_env(tmp_path))

    assert result.exit_code == 0
    assert "consent: unset" in result.stdout
    assert "delivery-configured: no" in result.stdout
    assert "effective: enabled" in result.stdout
    assert "reason: default_enabled" in result.stdout
    assert "anonymous-id: not-created" in result.stdout
    assert f"state-file: {tmp_path / 'kickstart' / 'telemetry.json'}" in result.stdout


def test_enable_disable_and_status_preserve_identity(tmp_path: Path) -> None:
    runner = CliRunner()
    environment = _env(tmp_path)

    enabled = runner.invoke(app, ["telemetry", "enable"], env=environment)
    status = runner.invoke(app, ["telemetry", "status", "--json"], env=environment)
    disabled = runner.invoke(app, ["telemetry", "disable"], env=environment)

    assert enabled.exit_code == 0
    assert status.exit_code == 0
    assert disabled.exit_code == 0
    identity = json.loads(status.stdout)["anonymous_id"]
    assert identity is not None
    assert identity in enabled.stdout
    assert identity in disabled.stdout


def test_reset_reports_previous_identity_without_deleting_history(tmp_path: Path) -> None:
    runner = CliRunner()
    environment = _env(tmp_path)
    enabled = runner.invoke(app, ["telemetry", "enable"], env=environment)
    original_id = enabled.stdout.split("anonymous-id: ", maxsplit=1)[1].strip()

    reset = runner.invoke(app, ["telemetry", "reset-id"], env=environment)

    assert reset.exit_code == 0
    assert f"previous-anonymous-id: {original_id}" in reset.stdout
    assert "Historical events are not deleted" in reset.stdout


def test_disable_before_enable_does_not_create_an_identity(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["telemetry", "disable"], env=_env(tmp_path))

    assert result.exit_code == 0
    assert "anonymous-id: not-created" in result.stdout


def test_reset_before_enable_is_a_read_only_noop(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["telemetry", "reset-id"], env=_env(tmp_path))

    assert result.exit_code == 0
    assert "No telemetry ID exists; nothing was changed." in result.stdout
    assert not (tmp_path / "kickstart" / "telemetry.json").exists()


@pytest.mark.parametrize(
    ("command", "method_name"),
    [("enable", "enable"), ("disable", "disable"), ("reset-id", "reset_id")],
)
def test_mutating_commands_report_state_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    method_name: str,
) -> None:
    def fail(_store: TelemetryStateStore) -> None:
        raise TelemetryStateError("synthetic state failure")

    monkeypatch.setattr(TelemetryStateStore, method_name, fail)

    result = CliRunner().invoke(app, ["telemetry", command], env=_env(tmp_path))

    assert result.exit_code == 1
    assert "Telemetry state error: synthetic state failure" in result.stderr


def test_malformed_state_reports_fail_closed_json_status(tmp_path: Path) -> None:
    state_path = tmp_path / "kickstart" / "telemetry.json"
    state_path.parent.mkdir()
    state_path.write_text("{bad json", encoding="utf-8")

    result = CliRunner().invoke(app, ["telemetry", "status", "--json"], env=_env(tmp_path))

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["consent"] == "invalid"
    assert payload["effective"] is False
    assert payload["reason"] == "invalid_state"
    assert payload["anonymous_id"] is None
