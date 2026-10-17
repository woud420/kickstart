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
    assert env["PY_CACHE_DIR"] == str(tmp_path / "python")
    assert env["PIP_CACHE_DIR"] == str(tmp_path / "pip")
    assert env["POETRY_CACHE_DIR"] == str(tmp_path / "poetry")
    assert env["POETRY_VIRTUALENVS_PATH"] == str(tmp_path / "poetry-venvs")
    assert env["CARGO_HOME"] == str(tmp_path / "cargo")
    assert env["CARGO_TARGET_DIR"] == str(tmp_path / "cargo-targets")
    assert env["GOCACHE"] == str(tmp_path / "go-build")
    assert env["GOMODCACHE"] == str(tmp_path / "go-mod")
    assert env["BUN_CACHE_DIR"] == str(tmp_path / "bun")
    assert env["BUN_INSTALL_CACHE_DIR"] == str(tmp_path / "bun" / "install")
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


def test_eval_and_prewarm_ignore_dependency_makefiles(tmp_path: Path) -> None:
    from scripts.generated_make_test_eval import run_make_tests

    component = _component(tmp_path, "service", kind="service")
    (component / "package.json").write_text("{}\n")
    dependency = component / "node_modules" / "dependency"
    dependency.mkdir(parents=True)
    (dependency / "Makefile").write_text("test:\n\t@false\ninstall:\n\t@false\n")
    (dependency / "package.json").write_text("{}\n")

    assert _prewarm_targets(tmp_path) == (component,)
    results = run_make_tests(tmp_path, timeout_seconds=5, workers=1, target="test", env=os.environ.copy())
    assert len(results) == 1 and results[0].path == component
    assert results[0].returncode == 0


def test_opt_in_cleanup_runs_only_after_a_leaf_target_and_preserves_source(tmp_path: Path) -> None:
    from scripts.generated_make_test_eval import run_make_tests

    component = _component(tmp_path, "leaf", kind="service")
    source = component / "main.py"
    source.write_text("print('source')\n")
    for name in (".venv", "node_modules", ".cache"):
        (component / name).mkdir()
        (component / name / "installed.txt").write_text("rebuildable")

    options = {"timeout_seconds": 5, "workers": 1, "target": "test", "env": os.environ.copy()}
    assert run_make_tests(tmp_path, **options)[0].cleaned_artifacts == ()
    assert (component / ".venv").is_dir()

    result = run_make_tests(tmp_path, **options, clean_completed=True)[0]
    assert result.returncode == 0 and result.cleaned_artifacts == (".venv", "node_modules", ".cache")
    assert not (component / ".venv").exists() and not (component / "node_modules").exists()
    assert not (component / ".cache").exists()
    assert source.read_text() == "print('source')\n"
    assert (component / "Makefile").is_file() and (component / ".kickstart/scaffold.json").is_file()


def test_cleanup_preserves_aggregate_roots_unknown_kinds_symlinks_and_files(tmp_path: Path) -> None:
    from scripts.generated_make_test_eval import _cleanup_component_dependencies

    aggregate = _component(tmp_path, "aggregate", kind="system")
    (aggregate / "node_modules").mkdir()
    for kind in ("system", "unknown", "manifest-error"):
        assert _cleanup_component_dependencies(aggregate, kind) == ()
        assert (aggregate / "node_modules").is_dir()

    leaf = _component(tmp_path, "leaf", kind="service")
    outside = tmp_path / "external-dependencies"
    outside.mkdir()
    (outside / "keep.txt").write_text("external")
    (leaf / "node_modules").symlink_to(outside, target_is_directory=True)
    (leaf / ".venv").write_text("authored file")
    assert _cleanup_component_dependencies(leaf, "service") == ()
    assert (outside / "keep.txt").read_text() == "external"
    assert (leaf / ".venv").read_text() == "authored file"


def test_cleanup_preserves_recorded_source_inside_a_cache_named_directory(tmp_path: Path) -> None:
    import json
    from scripts.generated_make_test_eval import _cleanup_component_dependencies

    component = _component(tmp_path, "leaf", kind="service")
    cache = component / ".cache"
    cache.mkdir()
    (cache / "authored.txt").write_text("recorded source")
    manifest = component / ".kickstart/scaffold.json"
    data = json.loads(manifest.read_text())
    data["ownership"] = {".cache/authored.txt": "seed"}
    manifest.write_text(json.dumps(data))
    assert _cleanup_component_dependencies(component, "service") == ()
    assert (cache / "authored.txt").read_text() == "recorded source"
