def test_help_output(tmp_path, kickstart_run):
    result = kickstart_run("--help", cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert "kickstart" in result.stdout
    assert "create" in result.stdout
