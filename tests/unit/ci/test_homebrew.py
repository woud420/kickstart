from pathlib import Path
import hashlib
import subprocess

import pytest

from ci.homebrew import PLATFORMS, render_formula


@pytest.fixture
def archives(tmp_path: Path) -> Path:
    for platform in PLATFORMS:
        path = tmp_path / f"kickstart-{platform}-py3.14.tar.gz"
        path.write_bytes(platform.encode())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(".gz.sha256").write_text(f"{digest}  dist/{path.name}\n")
    return tmp_path


def test_formula_pins_every_platform_to_verified_release_assets(archives: Path) -> None:
    formula = render_formula("v1.2.3", archives)
    assert formula.count('sha256 "') == 4
    for platform in PLATFORMS:
        assert f"/releases/download/v1.2.3/kickstart-{platform}-py3.14.tar.gz" in formula
        assert hashlib.sha256(platform.encode()).hexdigest() in formula


@pytest.mark.parametrize("tag", ["latest", "v1.2.3-rc.1", "v1.2", 'v1.2.3"', "v01.2.3"])
def test_formula_rejects_non_stable_versions(archives: Path, tag: str) -> None:
    with pytest.raises(ValueError, match="stable"):
        render_formula(tag, archives)


def test_formula_refuses_missing_or_corrupt_release_assets(archives: Path) -> None:
    archive = archives / "kickstart-linux-x64-py3.14.tar.gz"
    archive.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        render_formula("v1.2.3", archives)
    archive.unlink()
    with pytest.raises(FileNotFoundError):
        render_formula("v1.2.3", archives)


def test_formula_refuses_checksum_for_wrong_asset(archives: Path) -> None:
    checksum = archives / "kickstart-linux-x64-py3.14.tar.gz.sha256"
    checksum.write_text(f"{'0' * 64}  another-asset.tar.gz\n")
    with pytest.raises(ValueError, match="Invalid checksum"):
        render_formula("v1.2.3", archives)


@pytest.mark.parametrize("command", ["install", "upgrade", "uninstall", "_managed-layout-handoff"])
@pytest.mark.parametrize("separator", [[], ["--"]])
def test_homebrew_launcher_refuses_self_management_before_running_payload(
    archives: Path, command: str, separator: list[str], tmp_path: Path
) -> None:
    formula = render_formula("v1.2.3", archives)
    launcher = formula.split('    (bin/"kickstart").write <<~SH\n', 1)[1].split("    SH\n", 1)[0]
    launcher = "\n".join(line.removeprefix("      ") for line in launcher.splitlines())
    script = tmp_path / "launcher"
    script.write_text(launcher.replace("#{libexec}", "/does-not-exist"))
    result = subprocess.run(["sh", str(script), *separator, command, "--force"], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Homebrew manages" in result.stderr
