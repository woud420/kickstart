from unittest.mock import patch

import pytest

from src.utils.errors import KickstartError, TemplateError
from src.utils.fs import TemplateEngine, write_file

def test_write_file_with_path_template(tmp_path):
    template_path = tmp_path / "template.txt"
    template_path.write_text("Hello {{NAME}}")
    
    output_path = tmp_path / "output.txt"
    write_file(output_path, template_path, name="World")
    
    assert output_path.exists()
    assert output_path.read_text() == "Hello World"

def test_write_file_with_string_template(tmp_path):
    output_path = tmp_path / "output.txt"
    write_file(output_path, "Hello {{NAME}}", name="World")
    
    assert output_path.exists()
    assert output_path.read_text() == "Hello World"

def test_write_file_creates_parent_directories(tmp_path):
    output_path = tmp_path / "subdir" / "output.txt"
    write_file(output_path, "Hello {{NAME}}", name="World")
    
    assert output_path.exists()
    assert output_path.parent.exists()
    assert output_path.read_text() == "Hello World"

def test_write_file_with_multiple_variables(tmp_path):
    output_path = tmp_path / "output.txt"
    write_file(output_path, "Hello {{NAME}} from {{PLACE}}", name="World", place="Earth")
    
    assert output_path.exists()
    assert output_path.read_text() == "Hello World from Earth"

def test_write_file_with_no_variables(tmp_path):
    output_path = tmp_path / "output.txt"
    write_file(output_path, "Hello World")

    assert output_path.exists()
    assert output_path.read_text() == "Hello World"

def test_render_string_with_invalid_syntax_raises_kickstart_template_error():
    engine = TemplateEngine()

    with pytest.raises(TemplateError) as exc_info:
        engine.render_string("Hello {% if name %}", {"name": "World"})

    assert isinstance(exc_info.value, KickstartError)
    assert exc_info.value.__cause__ is not None

def test_render_template_with_invalid_syntax_raises_kickstart_template_error(tmp_path):
    template_path = tmp_path / "broken.txt"
    template_path.write_text("Hello {% if name %}")

    engine = TemplateEngine()

    with pytest.raises(TemplateError) as exc_info:
        engine.render_template(template_path, {"name": "World"})

    assert isinstance(exc_info.value, KickstartError)
    assert exc_info.value.__cause__ is not None


def test_write_file_with_broken_path_template_warns_and_uses_legacy_substitution(tmp_path):
    template_path = tmp_path / "broken.txt"
    template_path.write_text("Hello {{NAME}} {% if broken %}")
    output_path = tmp_path / "output.txt"

    with patch("src.utils.fs.warn") as mock_warn:
        write_file(output_path, template_path, name="World")

    assert output_path.read_text() == "Hello World {% if broken %}"
    mock_warn.assert_called_once()
    assert "legacy {{NAME}} substitution" in mock_warn.call_args.args[0]


def test_write_file_with_broken_inline_template_warns_and_uses_legacy_substitution(tmp_path):
    output_path = tmp_path / "output.txt"

    with patch("src.utils.fs.warn") as mock_warn:
        write_file(output_path, "Hello {{NAME}} {% if broken %}", name="World")

    assert output_path.read_text() == "Hello World {% if broken %}"
    mock_warn.assert_called_once()
    assert "legacy {{NAME}} substitution" in mock_warn.call_args.args[0]
