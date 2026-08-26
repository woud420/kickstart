#!/usr/bin/env python3
"""Build report-only architecture evidence without importing target code.

This is the repository CI adapter for the portable analyze-graph-evolution
skill.  It invokes only Git and the hash-locked code-review-graph CLI, treats
the checkout as bytes, writes generated evidence outside the repository, and
keeps topology, CRG heuristics, behavior, and Delphi judgment in separate
lanes.
"""

from __future__ import annotations

import argparse
import base64
import copy
import fnmatch
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

GRAPH_SCHEMA = "graph-evidence/1.0.0"
BEHAVIOR_SCHEMA = "behavior-evidence/1.0.0"
DELPHI_SCHEMA = "delphi-rounds/1.0.0"
MANIFEST_SCHEMA = "architecture-evidence-artifact/1.0.0"
EVALUATOR_VERSION = "1.0.0"
NORMALIZER_VERSION = "graph-normalizer/1.1.0"
NORMALIZER_CONTRACT = (
    "absolute checkout prefix to repository-relative POSIX path; reject parent "
    "traversal; preserve case; entity paths resolve only when CRG node file_path "
    "is unique; canonical sort nodes and edges; remove CRG export clock fields"
)
SANDBOX_VERSION = "crg-subprocess-sandbox/1.0.0"
CRG_LAUNCHER_SOURCE = "from code_review_graph.cli import main; main()"
SANDBOX_PROBE_SOURCE = (
    "import os, sitecustomize, socket, sys; "
    "assert sitecustomize.NETWORK_SANDBOX_ACTIVE; "
    "assert socket.socket.connect.__module__ == 'sitecustomize'; "
    "assert '' not in sys.path; "
    "assert os.getcwd() not in {os.path.abspath(item) for item in sys.path if item}"
)
NETWORK_GUARD_SOURCE = '''\
"""Deny Python network access in the CRG subprocess."""
import socket

NETWORK_SANDBOX_ACTIVE = True

def _deny_network(*_args, **_kwargs):
    raise RuntimeError("network access denied by graph-evidence sandbox")

socket.create_connection = _deny_network
socket.socket.connect = _deny_network
socket.socket.connect_ex = _deny_network
'''
CRG_FIXED_ENVIRONMENT = {
    "ALL_PROXY": "http://127.0.0.1:9",
    "CRG_LEIDEN_SEED": "42",
    "CRG_SERIAL_PARSE": "1",
    "GIT_ALLOW_PROTOCOL": "file",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "HTTP_PROXY": "http://127.0.0.1:9",
    "HTTPS_PROXY": "http://127.0.0.1:9",
    "LANG": "C",
    "LC_ALL": "C",
    "NO_COLOR": "1",
    "NO_PROXY": "",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TERM": "dumb",
    "TZ": "UTC",
    "all_proxy": "http://127.0.0.1:9",
    "http_proxy": "http://127.0.0.1:9",
    "https_proxy": "http://127.0.0.1:9",
    "no_proxy": "",
}
COMPARABILITY_DIGESTS = (
    "analyzer",
    "analyzer_distribution",
    "dependency_lock",
    "policy",
    "normalizer",
    "corpus",
    "harness",
    "environment",
    "evaluator",
    "runtime",
    "sandbox",
)
EVALUATOR_CONFIGURATION_PATHS = (
    ".github/graph-metrics.yml",
    ".github/behavior-evidence.yml",
    ".github/graph-metrics-requirements.lock",
    ".github/workflows/graph-metrics.yml",
    ".github/workflows/graph-metrics-publish.yml",
    ".github/scripts/",
)
ALLOWED_CRG_COMMANDS = {"build", "status", "visualize", "detect-changes"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SCRIPT = Path(__file__).resolve()


class EvidenceError(RuntimeError):
    """Evidence cannot be produced without weakening the contract."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def sandbox_digest() -> str:
    return digest_bytes(
        canonical_bytes(
            {
                "version": SANDBOX_VERSION,
                "fixed_environment": CRG_FIXED_ENVIRONMENT,
                "launcher_sha256": digest_bytes(CRG_LAUNCHER_SOURCE.encode("utf-8")),
                "network_guard_sha256": digest_bytes(NETWORK_GUARD_SOURCE.encode("utf-8")),
                "probe_sha256": digest_bytes(SANDBOX_PROBE_SOURCE.encode("utf-8")),
                "path_policy": "generated directory containing only a symlink to measured git",
                "dynamic_paths": [
                    "CRG_DATA_DIR",
                    "HOME",
                    "MPLCONFIGDIR",
                    "PATH",
                    "PYTHONPATH",
                    "PYTHONPYCACHEPREFIX",
                    "TMPDIR",
                    "XDG_CACHE_HOME",
                    "XDG_CONFIG_HOME",
                    "XDG_DATA_HOME",
                ],
            }
        )
    )


def evidence_policy_digest(
    graph_policy: Mapping[str, Any],
    behavior_policy: Mapping[str, Any],
) -> str:
    """Bind every graph and behavior policy field into comparability."""
    return digest_bytes(
        canonical_bytes(
            {
                "graph": graph_policy,
                "behavior": behavior_policy,
            }
        )
    )


def measured_runtime() -> dict[str, str]:
    system = platform.system()
    if system == "Linux":
        release = platform.freedesktop_os_release()
        operating_system = f"{release.get('ID', 'linux')}-{release.get('VERSION_ID', platform.release())}"
    elif system == "Darwin":
        operating_system = f"macos-{platform.mac_ver()[0]}"
    else:
        operating_system = f"{system.lower()}-{platform.release()}"
    machine = platform.machine().lower()
    architecture = {"amd64": "x86_64", "aarch64": "arm64"}.get(machine, machine)
    return {
        "os": operating_system,
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "architecture": architecture,
    }


def measure_analyzer_identity(crg_bin: Path) -> dict[str, Any]:
    executable = crg_bin.resolve()
    first_line = executable.read_text(encoding="utf-8", errors="strict").splitlines()[0]
    if not first_line.startswith("#!") or " " in first_line[2:]:
        raise EvidenceError("CRG console script does not have one absolute interpreter")
    interpreter = Path(first_line[2:]).resolve()
    if interpreter != Path(sys.executable).resolve():
        raise EvidenceError("CRG console script is not installed in the pinned Python runtime")
    try:
        distribution = importlib.metadata.distribution("code-review-graph")
    except importlib.metadata.PackageNotFoundError as exc:
        raise EvidenceError("installed code-review-graph distribution is unavailable") from exc
    entry_points = [
        entry
        for entry in distribution.entry_points
        if entry.group == "console_scripts" and entry.name == "code-review-graph"
    ]
    if len(entry_points) != 1 or entry_points[0].value != "code_review_graph.cli:main":
        raise EvidenceError("installed analyzer console entry point is not the reviewed target")
    package_records: list[dict[str, Any]] = []
    for package_path in distribution.files or []:
        relative = PurePosixPath(str(package_path))
        if not relative.parts or relative.parts[0] != "code_review_graph":
            continue
        if "__pycache__" in relative.parts or relative.suffix == ".pyc":
            continue
        record_hash = package_path.hash
        if record_hash is None or record_hash.mode != "sha256":
            raise EvidenceError(f"installed analyzer file lacks a SHA-256 RECORD entry: {relative}")
        installed = Path(str(distribution.locate_file(package_path)))
        if not installed.is_file() or installed.is_symlink():
            raise EvidenceError(f"installed analyzer entry is not one regular file: {relative}")
        actual_hex = digest_file(installed)
        actual_record = base64.urlsafe_b64encode(bytes.fromhex(actual_hex)).decode("ascii").rstrip("=")
        if actual_record != record_hash.value:
            raise EvidenceError(f"installed analyzer file differs from wheel RECORD: {relative}")
        package_records.append({"path": relative.as_posix(), "sha256": actual_hex, "size": installed.stat().st_size})
    if not package_records:
        raise EvidenceError("installed analyzer distribution has no measured package files")
    package_records.sort(key=lambda record: str(record["path"]))
    return {
        "distribution_name": str(distribution.metadata.get("Name", "")),
        "version": distribution.version,
        "installed_code_sha256": digest_bytes(canonical_bytes(package_records)),
        "measured_file_count": len(package_records),
        "entry_point": entry_points[0].value,
    }


def structured_digest(value: Mapping[str, Any]) -> str:
    stable = copy.deepcopy(dict(value))
    stable.pop("artifact_digest", None)
    stable.pop("generated_at", None)
    return digest_bytes(canonical_bytes(stable))


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = copy.deepcopy(dict(value))
    payload["artifact_digest"] = structured_digest(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(payload))


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"expected a JSON object in {path}")
    return value


def run_checked(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise EvidenceError(f"command failed ({completed.returncode}): {command!r}: {detail}")
    return completed.stdout


def git(repo: Path, *args: str) -> str:
    return run_checked(["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args])


def resolve_executable(value: str) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_absolute() or "/" in value:
        resolved = candidate.resolve()
        if not resolved.is_file():
            raise EvidenceError(f"executable not found: {value}")
        return resolved
    located = shutil.which(value)
    if not located:
        raise EvidenceError(f"executable not found on PATH: {value}")
    return Path(located).resolve()


def validate_sha(value: str, label: str) -> str:
    normalized = value.lower()
    if not SHA_RE.fullmatch(normalized):
        raise EvidenceError(f"{label} must be a full 40-character commit SHA")
    return normalized


def resolve_revision(repo: Path, revision: str, label: str) -> str:
    resolved = git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").strip()
    validate_sha(resolved, label)
    return resolved


def commit_metadata(repo: Path, revision: str) -> dict[str, str]:
    raw = git(repo, "show", "-s", "--format=%H%x00%P%x00%cI%x00%T", revision).rstrip("\n")
    commit, parents, committed_at, tree = raw.split("\x00")
    return {"commit": commit, "parents": parents, "committed_at": committed_at, "tree": tree}


def repository_slug(repo: Path) -> str:
    try:
        remote = git(repo, "config", "--get", "remote.origin.url").strip()
    except EvidenceError:
        return ""
    match = re.search(r"(?:github\.com[:/])([^/]+/[^/]+?)(?:\.git)?$", remote)
    if match:
        return match.group(1)
    return PurePosixPath(remote).name.removesuffix(".git")


def ensure_scratch_output(repo: Path, output: Path) -> None:
    repo_resolved = repo.resolve()
    output_resolved = output.resolve()
    try:
        inside = os.path.commonpath([str(repo_resolved), str(output_resolved)]) == str(repo_resolved)
    except ValueError:
        inside = False
    if inside:
        raise EvidenceError(f"output must be outside the target repository: {output_resolved}")


def make_readonly_checkout(repo: Path, revision: str, destination: Path) -> Path:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_checked(["git", "clone", "--quiet", "--shared", "--no-checkout", str(repo), str(destination)])
    git(destination, "checkout", "--quiet", "--detach", revision)
    return destination


def strict_crg_environment(data_dir: Path) -> dict[str, str]:
    sandbox_root = data_dir.parent / "sandbox"
    tool_bin = sandbox_root / "bin"
    home = sandbox_root / "home"
    temporary = sandbox_root / "tmp"
    pycache = sandbox_root / "pycache"
    matplotlib = sandbox_root / "matplotlib"
    xdg_cache = sandbox_root / "xdg-cache"
    xdg_config = sandbox_root / "xdg-config"
    xdg_data = sandbox_root / "xdg-data"
    for directory in (tool_bin, home, temporary, matplotlib, xdg_cache, xdg_config, xdg_data):
        directory.mkdir(parents=True, exist_ok=True)
    if pycache.exists():
        shutil.rmtree(pycache)
    pycache.mkdir(parents=True)
    network_guard = sandbox_root / "sitecustomize.py"
    network_guard.write_text(NETWORK_GUARD_SOURCE, encoding="utf-8")
    git_target = resolve_executable("git")
    git_link = tool_bin / "git"
    if git_link.exists() or git_link.is_symlink():
        git_link.unlink()
    git_link.symlink_to(git_target)
    environment = dict(CRG_FIXED_ENVIRONMENT)
    environment.update(
        {
            "CRG_DATA_DIR": str(data_dir),
            "HOME": str(home),
            "MPLCONFIGDIR": str(matplotlib),
            "PATH": str(tool_bin),
            "PYTHONPATH": str(sandbox_root),
            "PYTHONPYCACHEPREFIX": str(pycache),
            "TMPDIR": str(temporary),
            "XDG_CACHE_HOME": str(xdg_cache),
            "XDG_CONFIG_HOME": str(xdg_config),
            "XDG_DATA_HOME": str(xdg_data),
        }
    )
    return environment


def normalized_crg_environment() -> dict[str, str]:
    """Record the effective environment without run-specific scratch paths."""
    environment = dict(CRG_FIXED_ENVIRONMENT)
    environment.update(
        {
            "CRG_DATA_DIR": "<scratch>/crg",
            "HOME": "<scratch>/home",
            "MPLCONFIGDIR": "<scratch>/matplotlib",
            "PATH": "<scratch>/bin",
            "PYTHONPATH": "<scratch>",
            "PYTHONPYCACHEPREFIX": "<scratch>/pycache",
            "TMPDIR": "<scratch>/tmp",
            "XDG_CACHE_HOME": "<scratch>/xdg-cache",
            "XDG_CONFIG_HOME": "<scratch>/xdg-config",
            "XDG_DATA_HOME": "<scratch>/xdg-data",
        }
    )
    return dict(sorted(environment.items()))


def verify_crg_sandbox(environment: Mapping[str, str], cwd: Path) -> None:
    run_checked(
        [sys.executable, "-P", "-c", SANDBOX_PROBE_SOURCE],
        cwd=cwd,
        env=environment,
    )


def run_crg_main(environment: Mapping[str, str], cwd: Path, *args: str) -> str:
    return run_checked(
        [sys.executable, "-P", "-c", CRG_LAUNCHER_SOURCE, *args],
        cwd=cwd,
        env=environment,
    )


def crg(_crg_bin: Path, repo: Path, data_dir: Path, command: str, *args: str) -> str:
    if command not in ALLOWED_CRG_COMMANDS:
        raise EvidenceError(f"refusing unsupported CRG command: {command}")
    environment = strict_crg_environment(data_dir)
    verify_crg_sandbox(environment, repo)
    return run_crg_main(environment, repo, command, "--repo", str(repo), *args)


def parse_crg_json(output: str) -> dict[str, Any]:
    start = output.find("{")
    if start < 0:
        raise EvidenceError("CRG did not emit a JSON object")
    try:
        value = json.loads(output[start:])
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid CRG JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError("CRG JSON must be an object")
    return value


def verify_inputs(policy: Mapping[str, Any], lock_path: Path, crg_bin: Path, identity_data_dir: Path) -> dict[str, Any]:
    if policy.get("schema_version") != GRAPH_SCHEMA:
        raise EvidenceError(f"policy schema must be {GRAPH_SCHEMA}")
    runtime_policy = policy.get("runtime", {})
    expected_lock = str(runtime_policy.get("dependency_lock_sha256", ""))
    actual_lock = digest_file(lock_path)
    if actual_lock != expected_lock:
        raise EvidenceError(f"dependency lock digest mismatch: expected {expected_lock}, got {actual_lock}")
    actual_runtime = measured_runtime()
    expected_runtime = {
        name: str(runtime_policy.get(name, "")) for name in ("os", "python", "python_implementation", "architecture")
    }
    if actual_runtime != expected_runtime:
        raise EvidenceError(f"runtime mismatch: expected {expected_runtime!r}, measured {actual_runtime!r}")
    declared_environment = runtime_policy.get("environment", {})
    for name in ("CRG_SERIAL_PARSE", "CRG_LEIDEN_SEED", "PYTHONHASHSEED", "TZ"):
        if str(declared_environment.get(name, "")) != CRG_FIXED_ENVIRONMENT[name]:
            raise EvidenceError(f"policy does not pin the effective CRG setting {name}")
    analyzer_policy = policy.get("analyzer", {})
    expected_name = str(analyzer_policy.get("name", ""))
    expected_version = str(analyzer_policy.get("version", ""))
    distribution_sha256 = str(analyzer_policy.get("distribution_sha256", ""))
    expected_code_sha256 = str(analyzer_policy.get("installed_code_sha256", ""))
    if not DIGEST_RE.fullmatch(distribution_sha256) or not DIGEST_RE.fullmatch(expected_code_sha256):
        raise EvidenceError("analyzer distribution and installed-code digests must be pinned")
    lock_text = lock_path.read_text(encoding="utf-8")
    if f"code-review-graph=={expected_version}" not in lock_text or f"sha256:{distribution_sha256}" not in lock_text:
        raise EvidenceError("dependency lock does not bind the declared analyzer version and wheel")
    identity = measure_analyzer_identity(crg_bin)
    normalized_name = str(identity["distribution_name"]).lower().replace("_", "-")
    if normalized_name != expected_name or identity["version"] != expected_version:
        raise EvidenceError(f"installed analyzer identity mismatch: {identity!r}")
    if identity["installed_code_sha256"] != expected_code_sha256:
        raise EvidenceError(
            "installed analyzer code differs from the measured policy digest: "
            f"expected {expected_code_sha256}, got {identity['installed_code_sha256']}"
        )
    identity_environment = strict_crg_environment(identity_data_dir)
    verify_crg_sandbox(identity_environment, identity_data_dir.parent)
    cli_version = run_crg_main(identity_environment, identity_data_dir.parent, "--version").strip()
    expected_cli_version = f"code-review-graph {expected_version}"
    if cli_version != expected_cli_version:
        raise EvidenceError(f"analyzer CLI version mismatch: expected {expected_cli_version}, got {cli_version}")
    identity["cli_version"] = cli_version
    return identity


def suffix_for(path: str) -> str:
    name = PurePosixPath(path).name
    if name.endswith(".tpl"):
        return ".tpl"
    return PurePosixPath(path).suffix.lower()


def path_included(path: str, corpus: Mapping[str, Any]) -> bool:
    included = any(fnmatch.fnmatch(path, str(pattern)) for pattern in corpus.get("include", ["**"]))
    excluded = any(fnmatch.fnmatch(path, str(pattern)) for pattern in corpus.get("exclude", []))
    return included and not excluded


def tracked_corpus(repo: Path, revision: str, corpus: Mapping[str, Any]) -> dict[str, Any]:
    raw = git(repo, "ls-tree", "-r", "-z", "--long", revision)
    source_suffixes = {str(value).lower() for value in corpus.get("source_suffixes", [])}
    template_suffixes = {str(value).lower() for value in corpus.get("template_suffixes", [".tpl"])}
    files: list[dict[str, Any]] = []
    for record in raw.split("\x00"):
        if not record:
            continue
        metadata, path = record.split("\t", 1)
        mode, kind, blob, size_raw = metadata.split()
        if kind != "blob" or not path_included(path, corpus):
            continue
        suffix = suffix_for(path)
        is_template = suffix in template_suffixes
        files.append(
            {
                "path": path,
                "blob": blob,
                "bytes": int(size_raw) if size_raw.isdigit() else 0,
                "suffix": suffix or "<none>",
                "source_like": suffix in source_suffixes or is_template,
                "template": is_template,
                "mode": mode,
            }
        )
    files.sort(key=lambda item: item["path"])
    return {
        "files": files,
        "definition_digest": digest_bytes(canonical_bytes(corpus)),
        "revision_digest": digest_bytes(canonical_bytes(files)),
    }


def normalize_path(raw: str, checkout: Path) -> str | None:
    value = raw.replace("\\", "/")
    root = str(checkout.resolve()).replace("\\", "/").rstrip("/")
    if value == root:
        return None
    if value.startswith(root + "/"):
        value = value[len(root) + 1 :]
    elif value.startswith("/"):
        return None
    value = str(PurePosixPath(value))
    if value == "." or value.startswith("../") or "/../" in value:
        return None
    return value


def map_graph(
    graph: Mapping[str, Any], checkout: Path, in_scope_paths: set[str]
) -> tuple[set[str], list[dict[str, Any]], dict[str, Any]]:
    entity_to_files: dict[str, set[str]] = defaultdict(set)
    file_nodes: set[str] = set()
    languages: dict[str, str] = {}
    for node in graph.get("nodes", []):
        if not isinstance(node, dict) or not isinstance(node.get("file_path"), str):
            continue
        normalized = normalize_path(str(node["file_path"]), checkout)
        if normalized is None or normalized not in in_scope_paths:
            continue
        qualified = node.get("qualified_name")
        name = node.get("name")
        if isinstance(qualified, str):
            entity_to_files[qualified].add(normalized)
        if isinstance(name, str) and name.startswith(str(checkout)):
            entity_to_files[name].add(normalized)
        if str(node.get("kind", "")).lower() == "file":
            file_nodes.add(normalized)
            languages[normalized] = str(node.get("language") or "unknown")

    def resolve_entity(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        candidates = entity_to_files.get(value, set())
        if len(candidates) == 1:
            return next(iter(candidates))
        if len(candidates) > 1:
            return None
        normalized = normalize_path(value.split("::", 1)[0], checkout)
        return normalized if normalized in in_scope_paths else None

    edges: list[dict[str, Any]] = []
    unresolved: dict[str, int] = defaultdict(int)
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        kind = str(edge.get("kind") or "unknown").upper()
        source = resolve_entity(edge.get("source"))
        target = resolve_entity(edge.get("target"))
        if source is None or target is None:
            unresolved[kind] += 1
            continue
        edges.append(
            {
                "source": source,
                "target": target,
                "kind": kind,
                "confidence": edge.get("confidence"),
                "confidence_tier": edge.get("confidence_tier"),
            }
        )
    edges.sort(key=lambda edge: (edge["kind"], edge["source"], edge["target"]))
    return (
        file_nodes,
        edges,
        {
            "languages": dict(sorted(languages.items())),
            "unresolved_edges_by_kind": dict(sorted(unresolved.items())),
            "ambiguous_entity_count": sum(len(paths) > 1 for paths in entity_to_files.values()),
        },
    )


def stable_export_stats(value: Any) -> dict[str, Any]:
    """Remove CRG clock fields while retaining deterministic export counters."""
    if not isinstance(value, dict):
        return {}
    return {
        str(key): copy.deepcopy(item)
        for key, item in sorted(value.items())
        if key not in {"last_updated", "generated_at", "timestamp"}
    }


def strongly_connected_components(nodes: Iterable[str], edges: Iterable[tuple[str, str]]) -> list[list[str]]:
    adjacency: dict[str, list[str]] = {node: [] for node in sorted(set(nodes))}
    for source, target in sorted(set(edges)):
        if source in adjacency and target in adjacency:
            adjacency[source].append(target)
    for targets in adjacency.values():
        targets.sort()
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency[node]:
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            members: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                members.append(member)
                if member == node:
                    break
            components.append(sorted(members))

    for node in sorted(adjacency):
        if node not in indices:
            visit(node)
    return sorted(components, key=lambda members: (-len(members), members))


def boundary_for(path: str, boundaries: Sequence[Mapping[str, Any]]) -> str:
    for boundary in boundaries:
        if any(path.startswith(str(prefix)) for prefix in boundary.get("prefixes", [])):
            return str(boundary["name"])
        if any(fnmatch.fnmatch(path, str(pattern)) for pattern in boundary.get("globs", [])):
            return str(boundary["name"])
    return "other"


def projection_metrics(
    nodes: set[str],
    edges: Sequence[Mapping[str, Any]],
    admitted_kinds: set[str],
    boundaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    selected = [edge for edge in edges if edge["kind"] in admitted_kinds]
    distinct = sorted({(str(edge["source"]), str(edge["target"])) for edge in selected})
    self_loops = {source for source, target in distinct if source == target}
    components = strongly_connected_components(nodes, distinct)
    cyclic_nodes: set[str] = set()
    cross_boundary: list[dict[str, str]] = []
    excess = 0
    sccs: list[dict[str, Any]] = []
    for members in components:
        cyclic = len(members) > 1 or bool(self_loops.intersection(members))
        if not cyclic:
            continue
        member_set = set(members)
        internal = [(source, target) for source, target in distinct if source in member_set and target in member_set]
        cyclic_nodes.update(members)
        excess += max(0, len(internal) - len(members))
        for source, target in internal:
            source_boundary = boundary_for(source, boundaries)
            target_boundary = boundary_for(target, boundaries)
            if source_boundary != target_boundary:
                cross_boundary.append(
                    {
                        "source": source,
                        "target": target,
                        "source_boundary": source_boundary,
                        "target_boundary": target_boundary,
                    }
                )
        sccs.append(
            {
                "id": digest_bytes(canonical_bytes(members)),
                "members": members,
                "node_count": len(members),
                "internal_edge_count": len(internal),
            }
        )
    fan_in = {node: 0 for node in nodes}
    fan_out = {node: 0 for node in nodes}
    for source, target in distinct:
        fan_out[source] += 1
        fan_in[target] += 1
    confidence_counts: dict[str, int] = defaultdict(int)
    for edge in selected:
        confidence_counts[str(edge.get("confidence_tier") or "unknown")] += 1
    return {
        "admitted_edge_kinds": sorted(admitted_kinds),
        "confidence_tiers": dict(sorted(confidence_counts.items())),
        "node_count": len(nodes),
        "edge_count": len(distinct),
        "edge_multiplicity_count": len(selected),
        "self_loop_count": len(self_loops),
        "largest_scc_nodes": max((record["node_count"] for record in sccs), default=0),
        "cyclic_nodes": len(cyclic_nodes),
        "cyclic_node_proportion": round(len(cyclic_nodes) / len(nodes), 8) if nodes else 0.0,
        "cycle_mass": len(cyclic_nodes),
        "excess_cyclic_edges": excess,
        "cross_boundary_cyclic_edge_count": len(cross_boundary),
        "cross_boundary_cyclic_edges": sorted(cross_boundary, key=lambda item: (item["source"], item["target"])),
        "sccs": sccs,
        "edges": [{"source": source, "target": target} for source, target in distinct],
        "fan_in": dict(sorted(fan_in.items())),
        "fan_out": dict(sorted(fan_out.items())),
        "top_fan_in": [
            {"path": path, "value": value}
            for path, value in sorted(fan_in.items(), key=lambda item: (-item[1], item[0]))[:20]
        ],
        "top_fan_out": [
            {"path": path, "value": value}
            for path, value in sorted(fan_out.items(), key=lambda item: (-item[1], item[0]))[:20]
        ],
    }


def parser_coverage(
    corpus_result: Mapping[str, Any],
    parsed_files: set[str],
    language_by_path: Mapping[str, str],
) -> dict[str, Any]:
    source = [item for item in corpus_result["files"] if item["source_like"]]
    parsed = [item for item in source if item["path"] in parsed_files]
    unsupported = [item for item in source if item["path"] not in parsed_files]
    source_bytes = sum(int(item["bytes"]) for item in source)
    parsed_bytes = sum(int(item["bytes"]) for item in parsed)
    groups: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "bytes": 0})
    for item in unsupported:
        groups[str(item["suffix"])]["files"] += 1
        groups[str(item["suffix"])]["bytes"] += int(item["bytes"])
    languages: dict[str, int] = defaultdict(int)
    for item in parsed:
        path = str(item["path"])
        languages[str(language_by_path.get(path, "unknown"))] += 1
    return {
        "source_like_files": len(source),
        "source_like_bytes": source_bytes,
        "parsed_files": len(parsed),
        "parsed_bytes": parsed_bytes,
        "file_coverage": round(len(parsed) / len(source), 8) if source else 1.0,
        "byte_coverage": round(parsed_bytes / source_bytes, 8) if source_bytes else 1.0,
        "parser_languages": dict(sorted(languages.items())),
        "unsupported_count": len(unsupported),
        "unsupported_by_suffix": dict(sorted(groups.items())),
        "unsupported_files": [str(item["path"]) for item in unsupported],
    }


def environment_manifest(analyzer_identity: Mapping[str, Any]) -> dict[str, Any]:
    git_executable = resolve_executable("git")
    return {
        "runtime": measured_runtime(),
        "git": run_checked([str(git_executable), "--version"], env={"LANG": "C", "LC_ALL": "C"}).strip(),
        "git_executable_sha256": digest_file(git_executable),
        "crg_distribution_name": analyzer_identity["distribution_name"],
        "crg_cli_version": analyzer_identity["cli_version"],
        "crg_version": analyzer_identity["version"],
        "crg_installed_code_sha256": analyzer_identity["installed_code_sha256"],
        "filesystem_encoding": sys.getfilesystemencoding(),
        "runner_image_os": os.environ.get("ImageOS", ""),
        "runner_image_version": os.environ.get("ImageVersion", ""),
        "effective_crg_environment": normalized_crg_environment(),
        "subprocess_environment_policy": "strict allowlist; no inherited host variables",
        "network_policy": "Python sockets denied; Git protocols limited to file; HTTP proxies fail closed",
        "sandbox_version": SANDBOX_VERSION,
    }


def snapshot_from_graph(
    *,
    repo: Path,
    checkout: Path,
    revision: str,
    policy: Mapping[str, Any],
    policy_digest: str,
    lock_path: Path,
    analyzer_identity: Mapping[str, Any],
    graph: Mapping[str, Any],
    status: Mapping[str, Any],
) -> dict[str, Any]:
    metadata = commit_metadata(repo, revision)
    corpus = tracked_corpus(repo, revision, policy["corpus"])
    in_scope = {str(item["path"]) for item in corpus["files"]}
    parsed_files, edges, mapping = map_graph(graph, checkout, in_scope)
    boundaries = list(policy.get("boundaries", []))
    projections = {
        name: projection_metrics(parsed_files, edges, {str(kind).upper() for kind in kinds}, boundaries)
        for name, kinds in sorted(policy["projections"].items())
    }
    environment = environment_manifest(analyzer_identity)
    normalizer = digest_bytes(canonical_bytes({"version": NORMALIZER_VERSION, "contract": NORMALIZER_CONTRACT}))
    runtime = measured_runtime()
    digests = {
        "analyzer": str(analyzer_identity["installed_code_sha256"]),
        "analyzer_distribution": str(policy["analyzer"]["distribution_sha256"]),
        "dependency_lock": digest_file(lock_path),
        "policy": policy_digest,
        "normalizer": normalizer,
        "corpus": corpus["definition_digest"],
        "revision_corpus": corpus["revision_digest"],
        "environment": digest_bytes(canonical_bytes(environment)),
        "evaluator": digest_file(SCRIPT),
        "runtime": digest_bytes(canonical_bytes(runtime)),
        "sandbox": sandbox_digest(),
    }
    return {
        "schema_version": GRAPH_SCHEMA,
        "artifact_type": "snapshot",
        "generated_at": metadata["committed_at"],
        "producer": {"name": SCRIPT.name, "version": EVALUATOR_VERSION, "digest": digest_file(SCRIPT)},
        "repository": {
            "slug": repository_slug(repo),
            "revision": metadata["commit"],
            "tree": metadata["tree"],
            "parents": metadata["parents"].split() if metadata["parents"] else [],
        },
        "digests": digests,
        "environment": environment,
        "parser": parser_coverage(corpus, parsed_files, mapping["languages"]),
        "topology": {"status": "collected", "projections": projections},
        "crg": {
            "status": "collected",
            "analyzer": {
                "name": str(policy["analyzer"]["name"]),
                "version": str(policy["analyzer"]["version"]),
                "distribution_sha256": str(policy["analyzer"]["distribution_sha256"]),
                "installed_code_sha256": str(analyzer_identity["installed_code_sha256"]),
                "measured_file_count": int(analyzer_identity["measured_file_count"]),
                "entry_point": str(analyzer_identity["entry_point"]),
            },
            "database_stats": {key: status.get(key) for key in ("nodes", "edges", "files", "languages")},
            "export_stats": stable_export_stats(graph.get("stats", {})),
            "mapped_edge_count": len(edges),
            "unresolved_edges_by_kind": mapping["unresolved_edges_by_kind"],
            "ambiguous_entity_count": mapping["ambiguous_entity_count"],
            "risk": {"status": "not_collected_for_snapshot"},
        },
        "behavior": {"status": "not_collected"},
        "delphi": {"status": "not_collected"},
    }


def collect_snapshot(
    repo: Path,
    revision: str,
    output: Path,
    policy: Mapping[str, Any],
    policy_digest: str,
    lock_path: Path,
    crg_bin: Path,
    analyzer_identity: Mapping[str, Any],
    label: str,
) -> dict[str, Any]:
    scratch = output / ".scratch" / label
    checkout = make_readonly_checkout(repo, revision, scratch / "checkout")
    data_dir = scratch / "crg"
    data_dir.mkdir(parents=True, exist_ok=True)
    crg(crg_bin, checkout, data_dir, "build", "--skip-postprocess")
    status = parse_crg_json(crg(crg_bin, checkout, data_dir, "status", "--json"))
    crg(crg_bin, checkout, data_dir, "visualize", "--format", "json")
    graph_path = data_dir / "graph.json"
    if not graph_path.is_file():
        raise EvidenceError(f"CRG did not write expected graph export: {graph_path}")
    return snapshot_from_graph(
        repo=repo,
        checkout=checkout,
        revision=revision,
        policy=policy,
        policy_digest=policy_digest,
        lock_path=lock_path,
        analyzer_identity=analyzer_identity,
        graph=load_json(graph_path),
        status=status,
    )


def edge_set(projection: Mapping[str, Any]) -> set[tuple[str, str]]:
    return {(str(edge["source"]), str(edge["target"])) for edge in projection.get("edges", [])}


def cyclic_membership(projection: Mapping[str, Any]) -> dict[str, str]:
    return {str(member): str(scc["id"]) for scc in projection.get("sccs", []) for member in scc.get("members", [])}


def compare_projection(base: Mapping[str, Any], head: Mapping[str, Any]) -> dict[str, Any]:
    base_edges = edge_set(base)
    head_edges = edge_set(head)
    base_membership = cyclic_membership(base)
    head_membership = cyclic_membership(head)
    added = sorted(head_edges - base_edges)
    removed = sorted(base_edges - head_edges)
    new_cycle_edges = [
        (source, target)
        for source, target in added
        if source in head_membership
        and head_membership.get(source) == head_membership.get(target)
        and base_membership.get(source) != base_membership.get(target)
    ]
    persistence: list[dict[str, Any]] = []
    for head_scc in head.get("sccs", []):
        head_members = set(head_scc["members"])
        candidates: list[tuple[float, str, set[str]]] = []
        for base_scc in base.get("sccs", []):
            base_members = set(base_scc["members"])
            union = head_members | base_members
            score = len(head_members & base_members) / len(union) if union else 1.0
            candidates.append((score, str(base_scc["id"]), base_members))
        score, base_id, base_members = (
            max(candidates, key=lambda item: (item[0], item[1])) if candidates else (0.0, "", set())
        )
        persistence.append(
            {
                "head_scc_id": head_scc["id"],
                "base_scc_id": base_id or None,
                "jaccard": round(score, 8),
                "retained": sorted(head_members & base_members),
                "entered": sorted(head_members - base_members),
                "exited": sorted(base_members - head_members),
            }
        )
    fan_changes = []
    paths = set(base.get("fan_in", {})) | set(head.get("fan_in", {}))
    for path in paths:
        fan_changes.append(
            {
                "path": path,
                "fan_in_delta": int(head.get("fan_in", {}).get(path, 0)) - int(base.get("fan_in", {}).get(path, 0)),
                "fan_out_delta": int(head.get("fan_out", {}).get(path, 0)) - int(base.get("fan_out", {}).get(path, 0)),
            }
        )
    fan_changes.sort(key=lambda item: (-max(abs(item["fan_in_delta"]), abs(item["fan_out_delta"])), item["path"]))
    scalar_names = (
        "node_count",
        "edge_count",
        "largest_scc_nodes",
        "cyclic_nodes",
        "cyclic_node_proportion",
        "cycle_mass",
        "excess_cyclic_edges",
        "cross_boundary_cyclic_edge_count",
    )
    return {
        "deltas": {name: round(float(head.get(name, 0)) - float(base.get(name, 0)), 8) for name in scalar_names},
        "added_edges": [{"source": source, "target": target} for source, target in added],
        "removed_edges": [{"source": source, "target": target} for source, target in removed],
        "new_cycle_forming_edges": [{"source": source, "target": target} for source, target in new_cycle_edges],
        "scc_persistence": persistence,
        "fan_changes": fan_changes[:20],
    }


def summarize_crg_risk(raw: Mapping[str, Any]) -> dict[str, Any]:
    def first(*keys: str) -> Any:
        for key in keys:
            if key in raw and isinstance(raw[key], (str, int, float, bool, type(None))):
                return raw[key]
        return None

    def length(*keys: str) -> int | None:
        for key in keys:
            if isinstance(raw.get(key), list):
                return len(raw[key])
        return None

    return {
        "status": "collected",
        "risk_score": first("risk_score", "overall_risk_score", "score"),
        "risk_level": first("risk_level", "overall_risk", "level"),
        "changed_function_count": length("changed_functions", "functions"),
        "affected_file_count": length("affected_files", "files"),
        "test_gap_count": length("test_gaps", "missing_tests"),
        "raw_artifact_omitted": "Source snippets and absolute paths are not published.",
    }


def compare_snapshots(
    base: Mapping[str, Any],
    head: Mapping[str, Any],
    changed_paths: Sequence[str],
    configuration_paths: Sequence[str],
    risk: Mapping[str, Any],
) -> dict[str, Any]:
    mismatches = []
    if base.get("schema_version") != head.get("schema_version"):
        mismatches.append("schema_version")
    for name in COMPARABILITY_DIGESTS:
        if base.get("digests", {}).get(name) != head.get("digests", {}).get(name):
            mismatches.append(name)
    configured = set(str(path) for path in configuration_paths)
    configured.update(EVALUATOR_CONFIGURATION_PATHS)
    configuration_changed = any(
        path in configured or any(item.endswith("/") and path.startswith(item) for item in configured)
        for path in changed_paths
    )
    if configuration_changed:
        mismatches.append("configuration_changed")
    comparable = not mismatches
    topology = (
        {
            "status": "compared",
            "projections": {
                name: compare_projection(base["topology"]["projections"][name], head["topology"]["projections"][name])
                for name in sorted(base["topology"]["projections"])
            },
        }
        if comparable
        else {"status": "not_comparable", "projections": {}}
    )
    return {
        "schema_version": GRAPH_SCHEMA,
        "artifact_type": "comparison",
        "generated_at": head.get("generated_at"),
        "producer": {"name": SCRIPT.name, "version": EVALUATOR_VERSION, "digest": digest_file(SCRIPT)},
        "repository": {
            "slug": head.get("repository", {}).get("slug", ""),
            "base_revision": base.get("repository", {}).get("revision"),
            "head_revision": head.get("repository", {}).get("revision"),
        },
        "digests": dict(head.get("digests", {})),
        "comparison": {
            "status": "comparable" if comparable else "not_comparable",
            "reason": "comparable" if comparable else "not comparable; rebaseline required",
            "mismatches": sorted(set(mismatches)),
            "configuration_changed": configuration_changed,
            "changed_paths": sorted(changed_paths),
        },
        "parser": {
            "base": base.get("parser", {}),
            "head": head.get("parser", {}),
            "file_coverage_delta": round(
                float(head.get("parser", {}).get("file_coverage", 0))
                - float(base.get("parser", {}).get("file_coverage", 0)),
                8,
            ),
        },
        "topology": topology,
        "crg": {
            "status": "collected",
            "risk": summarize_crg_risk(risk),
            "warning": "CRG risk is heuristic and is not blended with topology metrics.",
        },
        "behavior": {"status": "not_collected"},
        "delphi": {"status": "not_collected"},
    }


def behavior_placeholder(
    policy: Mapping[str, Any], base_sha: str, head_sha: str, graph_digests: Mapping[str, Any]
) -> dict[str, Any]:
    policy_digest = digest_bytes(canonical_bytes(policy))
    harness = policy.get("harness", {})
    return {
        "schema_version": BEHAVIOR_SCHEMA,
        "artifact_type": "behavior-evidence",
        "generated_at": None,
        "producer": {"name": SCRIPT.name, "version": EVALUATOR_VERSION, "digest": digest_file(SCRIPT)},
        "repository": {"base_revision": base_sha, "head_revision": head_sha},
        "behavior": {
            "status": "not_collected",
            "change_intent": policy.get("change_intent", "preserve"),
            "evidence_result": "inconclusive",
            "comparability": {
                "status": "not_evaluated",
                "reason": "No frozen black-box observations were supplied to CI.",
            },
            "baseline_viable": None,
            "surfaces": policy.get("observable_surfaces", []),
            "matched_cases": [],
            "expected_differences": [],
            "unexpected_differences": [],
            "public_compatibility": {"status": "not_collected", "additions": [], "removals": []},
            "removed_or_weakened_assertions": policy.get("removed_or_weakened_assertions", []),
            "unmeasured_surfaces": policy.get("unmeasured_surfaces", []),
            "blocking_evidence_gaps": ["CI did not receive frozen base/head observation artifacts."],
            "residual_risk": policy.get("residual_risk", []),
        },
        "digests": {
            "policy": policy_digest,
            "dependency_lock": graph_digests.get("dependency_lock"),
            "environment": graph_digests.get("environment"),
            "harness": digest_bytes(canonical_bytes(harness)),
            "corpus": digest_bytes(canonical_bytes(policy.get("old_domain_case_ids", []))),
            "normalizer": digest_bytes(canonical_bytes({"normalizer": harness.get("normalizer")})),
        },
        "seed": harness.get("seed"),
    }


def delphi_placeholder(base_sha: str, head_sha: str) -> dict[str, Any]:
    return {
        "schema_version": DELPHI_SCHEMA,
        "artifact_type": "delphi-rounds",
        "generated_at": None,
        "producer": {"name": SCRIPT.name, "version": EVALUATOR_VERSION, "digest": digest_file(SCRIPT)},
        "repository": {"base_revision": base_sha, "head_revision": head_sha},
        "panel": {
            "label": "Delphi-inspired correlated agent panel",
            "facilitator_votes": False,
            "limitation": "CI has no LLM/API credentials; rounds run interactively through the portable skill.",
        },
        "status": "not_collected",
        "rounds": [],
        "outcome_reveal": {"status": "not_revealed"},
        "delphi": {"status": "not_collected"},
    }


def clean_markdown(value: Any, limit: int = 300) -> str:
    text = CONTROL_RE.sub("", str(value)).replace("|", "\\|").replace("@", "＠")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text[:limit] + ("…" if len(text) > limit else "")


def render_report(
    snapshot: Mapping[str, Any],
    comparison: Mapping[str, Any],
    behavior: Mapping[str, Any],
    delphi: Mapping[str, Any],
) -> str:
    decision = comparison.get("comparison", {})
    parser = snapshot.get("parser", {})
    lines = [
        "# Architecture evidence report",
        "",
        "> Report-only pilot. Machine topology, behavioral evidence, and Delphi-inspired judgment are independent lanes. No composite quality score is calculated.",
        "",
        f"Comparability: **{clean_markdown(decision.get('status', 'unknown'))}** — {clean_markdown(decision.get('reason', ''))}",
        "",
        "## Machine evidence",
        "",
        "| Parser coverage | Value |",
        "| --- | ---: |",
        f"| Source-like files | {clean_markdown(parser.get('source_like_files', 'unknown'))} |",
        f"| Parsed files | {clean_markdown(parser.get('parsed_files', 'unknown'))} |",
        f"| File coverage | {100 * float(parser.get('file_coverage', 0)):.1f}% |",
        f"| Byte coverage | {100 * float(parser.get('byte_coverage', 0)):.1f}% |",
        f"| Unsupported files | {clean_markdown(parser.get('unsupported_count', 'unknown'))} |",
        "",
    ]
    for name, projection in snapshot.get("topology", {}).get("projections", {}).items():
        delta = comparison.get("topology", {}).get("projections", {}).get(name, {}).get("deltas", {})
        lines += [f"### {clean_markdown(name)} projection", "", "| Metric | Current | Delta |", "| --- | ---: | ---: |"]
        for key in (
            "largest_scc_nodes",
            "cyclic_node_proportion",
            "cycle_mass",
            "excess_cyclic_edges",
            "cross_boundary_cyclic_edge_count",
        ):
            lines.append(
                f"| {key} | {clean_markdown(projection.get(key, 'unknown'))} | {clean_markdown(delta.get(key, 'n/a'))} |"
            )
        lines.append("")
    risk = comparison.get("crg", {}).get("risk", {})
    lines += [
        "CRG risk is shown separately because its resolution and risk model are heuristic.",
        "",
        f"- CRG risk level: `{clean_markdown(risk.get('risk_level', 'not reported'))}`",
        f"- CRG risk score: `{clean_markdown(risk.get('risk_score', 'not reported'))}`",
        "",
        "### Evidence identities",
        "",
    ]
    identities = snapshot.get("digests", {})
    for label, name in (
        ("Analyzer installed code", "analyzer"),
        ("Analyzer distribution", "analyzer_distribution"),
        ("Dependency lock", "dependency_lock"),
        ("Policy", "policy"),
        ("Normalizer", "normalizer"),
        ("Corpus definition", "corpus"),
        ("Behavior harness", "harness"),
        ("Environment", "environment"),
        ("Runtime", "runtime"),
        ("Evaluator", "evaluator"),
        ("CRG sandbox", "sandbox"),
    ):
        lines.append(f"- {label}: `{clean_markdown(identities.get(name, 'unknown'))}`")
    lines += [
        "",
        "## Behavioral evidence",
        "",
        f"- Change intent: `{clean_markdown(behavior.get('behavior', {}).get('change_intent', 'unknown'))}`",
        "- Evidence result: `inconclusive`",
        "- No frozen base/head black-box observation corpus was supplied to CI.",
        "",
        "## Delphi-inspired judgment",
        "",
        f"Panel: **{clean_markdown(delphi.get('panel', {}).get('label', 'Delphi-inspired correlated agent panel'))}**",
        "",
        "No locked interactive panel round is present. CI intentionally has no LLM/API credentials.",
        "",
        "## Historical study",
        "",
        "No historical cases are attached to this current-change run.",
        "",
        "## Guardrails",
        "",
        "- Report only; no merge gate and no automatic refactor.",
        "- A better topology result cannot compensate for contradicted or inconclusive behavior.",
        "- Production source changes require separate human approval.",
        "",
        f"Evaluator: `{digest_file(SCRIPT)}`",
        "",
    ]
    return "\n".join(lines)


def file_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "size": path.stat().st_size,
        "sha256": digest_file(path),
    }


def create_manifest(
    output: Path,
    policy: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    comparison: Mapping[str, Any],
    args: argparse.Namespace,
) -> None:
    files = [
        output / "snapshot.json",
        output / "comparison.json",
        output / "history.ndjson",
        output / "behavior-evidence.json",
        output / "delphi-rounds.json",
        output / "report.md",
    ]
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "artifact_type": "architecture-evidence-publication",
        "generated_at": snapshot.get("generated_at"),
        "producer": {"name": SCRIPT.name, "version": EVALUATOR_VERSION, "digest": digest_file(SCRIPT)},
        "workflow": {
            "repository": args.repository,
            "repository_id": args.repository_id,
            "run_id": args.run_id,
            "run_attempt": args.run_attempt,
            "event_name": args.event_name,
            "ref": args.ref,
        },
        "revision": {
            "base_sha": comparison.get("repository", {}).get("base_revision"),
            "head_sha": comparison.get("repository", {}).get("head_revision"),
            "pr_number": args.pr_number,
            "head_repository_id": args.head_repository_id,
        },
        "comparability": comparison.get("comparison", {}),
        "digests": snapshot.get("digests", {}),
        "publication": {
            "sticky_comment_marker": policy.get("publication", {}).get("sticky_comment_marker"),
            "report_only": True,
        },
        "files": [file_record(path, output) for path in files],
    }
    write_json(output / "manifest.json", manifest)


def collect_command(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    output = Path(args.output).resolve()
    policy_path = Path(args.policy).resolve()
    behavior_path = Path(args.behavior_policy).resolve()
    lock_path = Path(args.dependency_lock).resolve()
    ensure_scratch_output(repo, output)
    output.mkdir(parents=True, exist_ok=True)
    policy = load_json(policy_path)
    behavior_policy = load_json(behavior_path)
    policy_digest = evidence_policy_digest(policy, behavior_policy)
    crg_bin = resolve_executable(args.crg_bin)
    analyzer_identity = verify_inputs(policy, lock_path, crg_bin, output / ".scratch" / "identity" / "crg")
    base_sha = resolve_revision(repo, validate_sha(args.base, "base"), "base")
    head_sha = resolve_revision(repo, validate_sha(args.head, "head"), "head")
    base = collect_snapshot(
        repo,
        base_sha,
        output,
        policy,
        policy_digest,
        lock_path,
        crg_bin,
        analyzer_identity,
        "base",
    )
    head = collect_snapshot(
        repo,
        head_sha,
        output,
        policy,
        policy_digest,
        lock_path,
        crg_bin,
        analyzer_identity,
        "head",
    )
    harness_digest = digest_bytes(canonical_bytes(behavior_policy.get("harness", {})))
    base["digests"]["harness"] = harness_digest
    head["digests"]["harness"] = harness_digest
    changed_paths = [
        line for line in git(repo, "diff", "--name-only", "--no-renames", base_sha, head_sha).splitlines() if line
    ]
    head_checkout = output / ".scratch" / "head" / "checkout"
    head_data = output / ".scratch" / "head" / "crg"
    risk_raw = parse_crg_json(crg(crg_bin, head_checkout, head_data, "detect-changes", "--base", base_sha))
    comparison = compare_snapshots(
        base,
        head,
        changed_paths,
        [str(path) for path in policy.get("configuration_paths", [])],
        risk_raw,
    )
    behavior = behavior_placeholder(behavior_policy, base_sha, head_sha, head["digests"])
    delphi = delphi_placeholder(base_sha, head_sha)
    write_json(output / "snapshot.json", head)
    write_json(output / "comparison.json", comparison)
    write_json(output / "behavior-evidence.json", behavior)
    write_json(output / "delphi-rounds.json", delphi)
    (output / "history.ndjson").write_text("", encoding="utf-8")
    (output / "report.md").write_text(render_report(head, comparison, behavior, delphi), encoding="utf-8")
    create_manifest(output, policy, head, comparison, args)
    shutil.rmtree(output / ".scratch", ignore_errors=True)
    print(output / "manifest.json")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    directory = Path(args.directory).resolve()
    expected = {
        "snapshot.json": (GRAPH_SCHEMA, "snapshot"),
        "comparison.json": (GRAPH_SCHEMA, "comparison"),
        "behavior-evidence.json": (BEHAVIOR_SCHEMA, "behavior-evidence"),
        "delphi-rounds.json": (DELPHI_SCHEMA, "delphi-rounds"),
        "manifest.json": (MANIFEST_SCHEMA, "architecture-evidence-publication"),
    }
    for name, (schema, artifact_type) in expected.items():
        value = load_json(directory / name)
        if value.get("schema_version") != schema or value.get("artifact_type") != artifact_type:
            raise EvidenceError(f"{name}: invalid schema or artifact type")
        if value.get("artifact_digest") != structured_digest(value):
            raise EvidenceError(f"{name}: artifact digest mismatch")
    manifest = load_json(directory / "manifest.json")
    for record in manifest.get("files", []):
        path = directory / str(record["path"])
        if path.stat().st_size != record.get("size") or digest_file(path) != record.get("sha256"):
            raise EvidenceError(f"manifest file mismatch: {record.get('path')}")
    report = (directory / "report.md").read_text(encoding="utf-8")
    if "<script" in report.lower() or len(report.encode("utf-8")) > 60_000:
        raise EvidenceError("report.md is unsafe or oversized")
    print(f"verified artifacts in {directory}")
    return 0


def identity_command(args: argparse.Namespace) -> int:
    identity = measure_analyzer_identity(resolve_executable(args.crg_bin))
    print(canonical_bytes(identity).decode("utf-8"), end="")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    collect = subparsers.add_parser("collect")
    collect.add_argument("--repo", required=True)
    collect.add_argument("--output", required=True)
    collect.add_argument("--policy", required=True)
    collect.add_argument("--behavior-policy", required=True)
    collect.add_argument("--dependency-lock", required=True)
    collect.add_argument("--crg-bin", default="code-review-graph")
    collect.add_argument("--base", required=True)
    collect.add_argument("--head", required=True)
    collect.add_argument("--repository", required=True)
    collect.add_argument("--repository-id", required=True, type=int)
    collect.add_argument("--run-id", required=True, type=int)
    collect.add_argument("--run-attempt", required=True, type=int)
    collect.add_argument("--event-name", required=True)
    collect.add_argument("--ref", default="")
    collect.add_argument("--pr-number", type=int)
    collect.add_argument("--head-repository-id", type=int)
    collect.set_defaults(func=collect_command)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--directory", required=True)
    verify.set_defaults(func=verify_command)
    identity = subparsers.add_parser("identity")
    identity.add_argument("--crg-bin", default="code-review-graph")
    identity.set_defaults(func=identity_command)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return int(args.func(args))
    except (EvidenceError, OSError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
