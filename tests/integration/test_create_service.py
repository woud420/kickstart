import tempfile
from pathlib import Path


def test_create_python_service(kickstart_run):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        kickstart_run(
            "create", "service", "hello-api", "--lang", "python", "--root", str(tmp),
            cwd=tmp,
            check=True,
        )

        svc = tmp / "hello-api"
        assert (svc / "src").exists()
        assert (svc / "Dockerfile").exists()
        assert (svc / "README.md").read_text().startswith("# hello-api")


def test_create_python_service_with_root(kickstart_run):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        custom_root = tmp / "custom-root"
        custom_root.mkdir()

        kickstart_run(
            "create", "service", "hello-api", "--lang", "python", "--root", str(custom_root),
            cwd=tmp,
            check=True,
        )

        svc = custom_root / "hello-api"
        assert (svc / "src").exists()
        assert (svc / "Dockerfile").exists()
        assert (svc / "README.md").read_text().startswith("# hello-api")
