import pytest
from pathlib import Path
from src.utils.fs import write_file

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
