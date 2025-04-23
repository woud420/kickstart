import subprocess
from pathlib import Path
import tempfile
import shutil

def test_create_python_lib():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None, "kickstart binary not found in PATH"

        subprocess.run(
            [kickstart_bin, "create", "lib", "my-lib", "--lang", "python", "--root", str(tmp)],
            cwd=tmp,
            check=True
        )

        lib = tmp / "my-lib"
        assert (lib / "src").exists()
        assert (lib / "pyproject.toml").exists()
        assert (lib / "README.md").read_text().startswith("# my-lib")

def test_create_python_lib_with_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_bin = shutil.which("kickstart")
        assert kickstart_bin is not None, "kickstart binary not found in PATH"

        # Create a custom root directory
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        subprocess.run(
            [kickstart_bin, "create", "lib", "my-lib", "--lang", "python", "--root", str(custom_root)],
            cwd=tmp,
            check=True
        )

        lib = custom_root / "my-lib"
        assert (lib / "src").exists()
        assert (lib / "pyproject.toml").exists()
        assert (lib / "README.md").read_text().startswith("# my-lib") 