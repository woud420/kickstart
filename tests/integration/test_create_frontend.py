import subprocess
from pathlib import Path
import tempfile
import shutil

def test_create_frontend():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None, "kickstart binary not found in PATH"

        subprocess.run(
            [kickstart_bin, "create", "frontend", "my-app", "--root", str(tmp)],
            cwd=tmp,
            check=True
        )

        app = tmp / "my-app"
        assert (app / "src").exists()
        assert (app / "public").exists()
        assert (app / "package.json").exists()
        assert (app / "README.md").read_text().startswith("# my-app")

def test_create_frontend_with_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None, "kickstart binary not found in PATH"

        # Create a custom root directory
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        subprocess.run(
            [kickstart_bin, "create", "frontend", "my-app", "--root", str(custom_root)],
            cwd=tmp,
            check=True
        )

        app = custom_root / "my-app"
        assert (app / "src").exists()
        assert (app / "public").exists()
        assert (app / "package.json").exists()
        assert (app / "README.md").read_text().startswith("# my-app") 