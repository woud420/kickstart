import subprocess
import sys
from pathlib import Path
import tempfile
import os

def test_create_python_lib():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)

        subprocess.run(
            [
                sys.executable,
                str(repo_root / "kickstart.py"),
                "create",
                "lib",
                "my-lib",
                "--lang",
                "python",
                "--root",
                str(tmp),
                "--non-interactive",
            ],
            cwd=tmp,
            check=True,
            env=env,
        )

        lib = tmp / "my-lib"
        assert (lib / "src").exists()
        assert (lib / "pyproject.toml").exists()
        assert (lib / "README.md").read_text().startswith("# my-lib")

def test_create_python_lib_with_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)

        # Create a custom root directory
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        subprocess.run(
            [
                sys.executable,
                str(repo_root / "kickstart.py"),
                "create",
                "lib",
                "my-lib",
                "--lang",
                "python",
                "--root",
                str(custom_root),
                "--non-interactive",
            ],
            cwd=tmp,
            check=True,
            env=env,
        )

        lib = custom_root / "my-lib"
        assert (lib / "src").exists()
        assert (lib / "pyproject.toml").exists()
        assert (lib / "README.md").read_text().startswith("# my-lib") 
