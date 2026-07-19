import json
from pathlib import Path

from typer.testing import CliRunner

from src.cli.main import app


def _env(tmp_path: Path) -> dict[str, str]:
    return {
        "HOME": str(tmp_path),
        "POSTHOG_PUBLIC_CUSTOMER_API_TOKEN": "",
        "XDG_CONFIG_HOME": str(tmp_path),
    }


def test_status_is_read_only_before_opt_in(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["telemetry", "status", "--json"], env=_env(tmp_path))

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["consent"] == "unset"
    assert payload["delivery_configured"] is False
    assert payload["effective"] is False
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
