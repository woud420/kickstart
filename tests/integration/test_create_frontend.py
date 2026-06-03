import tempfile
from pathlib import Path


def test_create_frontend(kickstart_run):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_run(
            "create", "frontend", "my-app", "--root", str(tmp),
            cwd=tmp,
            check=True,
        )

        app = tmp / "my-app"
        assert (app / "src").exists()
        assert (app / "public").exists()
        assert (app / "package.json").exists()
        assert (app / "README.md").read_text().startswith("# my-app")


def test_create_frontend_with_root(kickstart_run):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        kickstart_run(
            "create", "frontend", "my-app", "--root", str(custom_root),
            cwd=tmp,
            check=True,
        )

        app = custom_root / "my-app"
        assert (app / "src").exists()
        assert (app / "public").exists()
        assert (app / "package.json").exists()
        assert (app / "README.md").read_text().startswith("# my-app")
