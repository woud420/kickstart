import tempfile
from pathlib import Path
import subprocess

def test_create_monorepo_kustomize():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        import shutil
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None

        subprocess.run([kickstart_bin, "create", "service", "hello-api", "--lang", "python"], cwd=tmp, check=True)

        base = tmp / "infra-stack"
        assert (base / "infra/k8s/base/deployment.yaml").exists()
        assert (base / "Makefile").exists()

