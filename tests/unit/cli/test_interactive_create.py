from typer.testing import CliRunner
from tests.unit.cli.command_helpers import CREATE

from src.cli.main import app


def test_interactive_create_service(tmp_path, monkeypatch):
    runner = CliRunner()
    recorded = {}

    def fake_create_service(name, lang, gh, config, helm=False, root=None):
        recorded["name"] = name
        recorded["root"] = root
        recorded["lang"] = lang

    monkeypatch.setattr(CREATE, "create_service", fake_create_service)
    monkeypatch.setattr(CREATE, "load_config", lambda: {})

    inputs = f"service\nmy-svc\n{tmp_path}\npython\nn\nn\nnone\nnone\nnone\nfastapi\n"
    result = runner.invoke(app, ["create"], input=inputs)
    assert result.exit_code == 0
    assert recorded["name"] == "my-svc"
    assert recorded["root"] == str(tmp_path)
