import subprocess
import sys
from pathlib import Path
import tempfile
import os

def test_create_frontend():
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
                "frontend",
                "my-app",
                "--root",
                str(tmp),
                "--non-interactive",
            ],
            cwd=tmp,
            check=True,
            env=env,
        )

        app = tmp / "my-app"
        assert (app / "src").exists()
        assert (app / "public").exists()
        assert (app / "package.json").exists()
        assert (app / "README.md").read_text().startswith("# my-app")

def test_create_frontend_with_root():
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
                "frontend",
                "my-app",
                "--root",
                str(custom_root),
                "--non-interactive",
            ],
            cwd=tmp,
            check=True,
            env=env,
        )

        app = custom_root / "my-app"
        assert (app / "src").exists()
        assert (app / "public").exists()
        assert (app / "package.json").exists()
        assert (app / "README.md").read_text().startswith("# my-app") 
