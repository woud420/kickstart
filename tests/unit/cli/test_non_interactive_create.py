from typer.testing import CliRunner

from src.cli.main import app
import src.cli.main as cli_main


def test_non_interactive_create_requires_args(tmp_path, monkeypatch):
    runner = CliRunner()

    result = runner.invoke(app, ["create", "service", "--non-interactive"])

    assert result.exit_code != 0
    assert "non-interactive mode requires" in result.stdout.lower()


def test_non_interactive_create_service(tmp_path, monkeypatch):
    runner = CliRunner()
    recorded = {}

    def fake_create_service(name, lang, gh, config, helm=False, root=None):
        recorded["name"] = name
        recorded["root"] = root

    monkeypatch.setattr(cli_main, "create_service", fake_create_service)
    monkeypatch.setattr(cli_main, "load_config", lambda: {})

    result = runner.invoke(
        app,
        ["create", "service", "my-svc", "--root", str(tmp_path), "--non-interactive"],
    )

    assert result.exit_code == 0
    assert recorded["name"] == "my-svc"
    assert recorded["root"] == str(tmp_path)

