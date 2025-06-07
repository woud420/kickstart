from typer.testing import CliRunner
from src.cli.main import app
import src.cli.main as cli_main


def test_interactive_create_service(tmp_path, monkeypatch):
    runner = CliRunner()
    recorded = {}

    def fake_create_service(name, lang, gh, config, helm=False, root=None):
        recorded['name'] = name
        recorded['root'] = root
        recorded['lang'] = lang

    monkeypatch.setattr(cli_main, 'create_service', fake_create_service)
    monkeypatch.setattr(cli_main, 'load_config', lambda: {})

    inputs = f"service\nmy-svc\n{tmp_path}\npython\nn\nn\n"
    result = runner.invoke(app, ['create'], input=inputs)
    assert result.exit_code == 0
    assert recorded['name'] == 'my-svc'
    assert recorded['root'] == str(tmp_path)
