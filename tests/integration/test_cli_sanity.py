import subprocess
import sys
import os
from pathlib import Path

def test_help_output(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)

    result = subprocess.run(
        [sys.executable, str(repo_root / "kickstart.py"), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "Kickstart" in result.stdout
    assert "create" in result.stdout
