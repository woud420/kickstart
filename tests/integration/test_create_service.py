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
            [kickstart_bin, "create", "service", "hello-api", "--lang", "python", "--root", str(tmp)],
            cwd=tmp,
            check=True
        )

        svc = tmp / "hello-api"
        assert (svc / "src").exists()
        assert (svc / "Dockerfile").exists()
        assert (svc / "README.md").read_text().startswith("# hello-api")

def test_create_python_service_with_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None, "kickstart binary not found in PATH"

        # Create a custom root directory
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        subprocess.run(
            [kickstart_bin, "create", "service", "hello-api", "--lang", "python", "--root", str(custom_root)],
            cwd=tmp,
            check=True
        )

        svc = custom_root / "hello-api"
        assert (svc / "src").exists()
        assert (svc / "Dockerfile").exists()
        assert (svc / "README.md").read_text().startswith("# hello-api")

