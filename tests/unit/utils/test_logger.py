import pytest

from src.utils.logger import error, info, success, warn


@pytest.mark.parametrize("emit", [info, success, warn, error])
def test_log_output_preserves_literal_message(emit, capsys):
    message = "Output directory: build/[red]preview[/red]"

    emit(message)

    assert message in capsys.readouterr().out
