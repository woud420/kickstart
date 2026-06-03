import tempfile
from pathlib import Path


def test_create_python_lib(kickstart_run):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_run(
            "create", "lib", "my-lib", "--lang", "python", "--root", str(tmp),
            cwd=tmp,
            check=True,
        )

        lib = tmp / "my-lib"
        assert (lib / "src").exists()
        assert (lib / "pyproject.toml").exists()
        assert (lib / "README.md").read_text().startswith("# my-lib")


def test_create_python_lib_with_root(kickstart_run):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        kickstart_run(
            "create", "lib", "my-lib", "--lang", "python", "--root", str(custom_root),
            cwd=tmp,
            check=True,
        )

        lib = custom_root / "my-lib"
        assert (lib / "src").exists()
        assert (lib / "pyproject.toml").exists()
        assert (lib / "README.md").read_text().startswith("# my-lib")
