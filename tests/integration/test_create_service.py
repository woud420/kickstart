import subprocess
from pathlib import Path
import tempfile
import shutil

def test_create_python_service():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None, "kickstart binary not found in PATH"

        subprocess.run(
            [kickstart_bin, "create", "service", "hello-api", "--lang", "python"],
            cwd=tmp,
            check=True
        )

        svc = tmp / "hello-api"
        assert (svc / "src").exists()
        assert (svc / "Dockerfile").exists()
        assert (svc / "README.md").read_text().startswith("# hello-api")

