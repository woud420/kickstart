import tempfile
from pathlib import Path
import subprocess
import sys
import os

def test_create_monorepo_kustomize():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)

        subprocess.run(
            [sys.executable, str(repo_root / "kickstart.py"), "create", "mono", "infra-stack", "--root", str(tmp)],
            cwd=tmp,
            check=True,
            env=env,
        )

        base = tmp / "infra-stack"
        assert (base / "infra/k8s/base/deployment.yaml").exists()
        assert (base / "Makefile").exists()

def test_create_monorepo_kustomize_with_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)

        # Create a custom root directory
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        subprocess.run(
            [sys.executable, str(repo_root / "kickstart.py"), "create", "mono", "infra-stack", "--root", str(custom_root)],
            cwd=tmp,
            check=True,
            env=env,
        )

        base = custom_root / "infra-stack"
        assert (base / "infra/k8s/base/deployment.yaml").exists()
        assert (base / "Makefile").exists()
