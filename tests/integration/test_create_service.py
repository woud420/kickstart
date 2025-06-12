import subprocess
import sys
from pathlib import Path
import tempfile
import os

def test_create_python_service():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)

        subprocess.run(
            [sys.executable, str(repo_root / "kickstart.py"), "create", "service", "hello-api", "--lang", "python", "--root", str(tmp)],
            cwd=tmp,
            check=True,
            env=env,
        )

        svc = tmp / "hello-api"
        assert (svc / "src").exists()
        assert (svc / "Dockerfile").exists()
        assert (svc / "README.md").read_text().startswith("# hello-api")

def test_create_python_service_with_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)

        # Create a custom root directory
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        subprocess.run(
            [sys.executable, str(repo_root / "kickstart.py"), "create", "service", "hello-api", "--lang", "python", "--root", str(custom_root)],
            cwd=tmp,
            check=True,
            env=env,
        )

        svc = custom_root / "hello-api"
        assert (svc / "src").exists()
        assert (svc / "Dockerfile").exists()
        assert (svc / "README.md").read_text().startswith("# hello-api")

