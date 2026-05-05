import os
from pathlib import Path

from scripts.generated_make_test_eval import (
    _classify_output,
    _prewarm_targets,
    _run_command,
    eval_environment,
)


def test_eval_environment_cached_sets_shared_tool_caches(tmp_path: Path) -> None:
    env = eval_environment("cached", tmp_path)

    assert env["XDG_CACHE_HOME"] == str(tmp_path / "xdg")
    assert env["PIP_CACHE_DIR"] == str(tmp_path / "pip")
    assert env["POETRY_CACHE_DIR"] == str(tmp_path / "poetry")
    assert env["POETRY_VIRTUALENVS_PATH"] == str(tmp_path / "poetry-venvs")
    assert env["CARGO_HOME"] == str(tmp_path / "cargo")
    assert env["CARGO_TARGET_DIR"] == str(tmp_path / "cargo-targets")
    assert env["GOCACHE"] == str(tmp_path / "go-build")
    assert env["GOMODCACHE"] == str(tmp_path / "go-mod")
    assert env["BUN_INSTALL_CACHE_DIR"] == str(tmp_path / "bun")
    assert env["npm_config_cache"] == str(tmp_path / "npm")
    assert (tmp_path / "go-build").is_dir()
    assert "PIP_NO_INDEX" not in env


def test_eval_environment_offline_sets_registry_offline_flags(tmp_path: Path) -> None:
    env = eval_environment("offline", tmp_path)

    assert env["CARGO_NET_OFFLINE"] == "true"
    assert env["GOPROXY"] == "off"
    assert env["PIP_NO_INDEX"] == "1"
    assert env["npm_config_offline"] == "true"


def test_classify_output_names_cache_network_registry_and_install_timeout() -> None:
    assert _classify_output("go-build: operation not permitted", 1, False) == "cache permission denied"
    assert _classify_output("Could not resolve host: registry.npmjs.org", 1, False) == "network unavailable"
    assert _classify_output("failed to resolve package version", 1, False) == "package registry unavailable"
    assert _classify_output("install still running", 124, True, target="install") == "timeout during dependency install"


def test_prewarm_targets_selects_one_makefile_per_dependency_family(tmp_path: Path) -> None:
    node_a = _component(tmp_path, "node-a", kind="service")
    _component(tmp_path, "node-b", kind="service")
    rust_a = _component(tmp_path, "rust-a", kind="service")
    docs_only = _component(tmp_path, "docs-only", kind="system")
    (node_a / "package.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "node-b" / "package.json").write_text("{}\n", encoding="utf-8")
    (rust_a / "Cargo.toml").write_text('[package]\nname = "rust-a"\n', encoding="utf-8")

    selected = _prewarm_targets(tmp_path)

    assert {path.name for path in selected} == {"node-a", "rust-a"}
    assert docs_only not in selected


def test_run_command_times_out_without_leaving_parent_process_running(tmp_path: Path) -> None:
    result = _run_command(
        ["/bin/sh", "-c", "sleep 30 & sleep 30"],
        cwd=tmp_path,
        timeout_seconds=1,
        env=os.environ.copy(),
    )

    assert result.returncode == 124
    assert result.timed_out is True


def _component(root: Path, name: str, *, kind: str) -> Path:
    path = root / name
    path.mkdir()
    (path / "Makefile").write_text("test:\n\t@true\ninstall:\n\t@true\n", encoding="utf-8")
    manifest_dir = path / ".kickstart"
    manifest_dir.mkdir()
    (manifest_dir / "scaffold.json").write_text(
        (
            "{\n"
            f'  "project": {{"kind": "{kind}"}},\n'
            '  "execution": {"platforms": ["container"]},\n'
            '  "artifacts": {"deploy": []}\n'
            "}\n"
        ),
        encoding="utf-8",
    )
    return path
