"""The project's own manifest is an accurate, enforceable adoption contract."""

from pathlib import Path
import shutil
import subprocess
import tomllib

from src.generator.adoption import inspect_repo
from src.generator.backstage_export import DEFAULT_OWNER, export_backstage
from src.generator.scaffold_contract import MANIFEST_PATH, ScaffoldContract, load_parsed_manifest


def test_repository_manifest_matches_its_cli_and_make_lifecycle(repo_root: Path) -> None:
    manifest = load_parsed_manifest(repo_root / MANIFEST_PATH)
    contract = ScaffoldContract.from_manifest(manifest)
    package = tomllib.loads((repo_root / "pyproject.toml").read_text())["project"]
    module = package["scripts"][package["name"]].split(":")[0]

    assert manifest["project"]["name"] == package["name"]
    assert contract.project_kind == "cli"
    assert contract.language == "python"
    assert contract.framework == contract.cli_framework == "typer"
    assert contract.entrypoint == module.replace(".", "/") + ".py"
    assert (repo_root / contract.entrypoint).is_file()
    assert contract.command_root == str(Path(contract.entrypoint).parent)
    assert contract.generated_by == "unknown"
    assert contract.ownership is not None
    for command in contract.resolved_lifecycle().manifest().values():
        executable, target = command.split()
        assert executable == "make"
        result = subprocess.run(["make", "--dry-run", target], cwd=repo_root, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


def test_repository_passes_its_read_only_adoption_check(repo_root: Path) -> None:
    paths = [repo_root / name for name in [MANIFEST_PATH, "Makefile", "AGENTS.md", "CLAUDE.md", "README.md"]]
    before = {path: path.read_bytes() for path in paths}

    report = inspect_repo(repo_root)

    assert report.complete, report.to_json()
    assert report.achieved_level == report.claimed_level == "managed"
    assert report.missing == ()
    assert {path: path.read_bytes() for path in paths} == before


def test_repository_manifest_exports_a_stable_backstage_tool(repo_root: Path, tmp_path: Path) -> None:
    (tmp_path / ".kickstart").mkdir()
    shutil.copyfile(repo_root / MANIFEST_PATH, tmp_path / MANIFEST_PATH)
    (tmp_path / "docs").mkdir()

    first = export_backstage(tmp_path)
    content = first.path.read_text()
    second = export_backstage(tmp_path)

    assert first.action == "created"
    assert first.issues == second.issues == ()
    assert "kind: Component" in content
    assert "name: kickstart" in content
    assert "type: tool" in content
    assert "lifecycle: experimental" in content
    assert f"owner: {DEFAULT_OWNER}" in content
    assert second.action == "unchanged"
    assert second.path.read_text() == content
