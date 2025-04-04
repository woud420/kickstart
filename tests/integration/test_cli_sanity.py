import subprocess

def test_help_output():
    result = subprocess.run(
        ["poetry", "run", "kickstart", "--help"],
        capture_output=True,
        text=True
    )
    assert "Kickstart" in result.stdout
    assert "create" in result.stdout

