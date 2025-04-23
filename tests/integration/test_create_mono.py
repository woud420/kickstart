import tempfile
from pathlib import Path
import subprocess
import shutil

def test_create_monorepo_kustomize():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None

        subprocess.run(
            [kickstart_bin, "create", "mono", "infra-stack", "--root", str(tmp)],
            cwd=tmp,
            check=True
        )

        base = tmp / "infra-stack"
        assert (base / "infra/k8s/base/deployment.yaml").exists()
        assert (base / "Makefile").exists()

def test_create_monorepo_kustomize_with_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None

        # Create a custom root directory
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        subprocess.run(
            [kickstart_bin, "create", "mono", "infra-stack", "--root", str(custom_root)],
            cwd=tmp,
            check=True
        )

        base = custom_root / "infra-stack"
        assert (base / "infra/k8s/base/deployment.yaml").exists()
        assert (base / "Makefile").exists()

