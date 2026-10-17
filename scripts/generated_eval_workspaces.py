"""Dependency ownership boundaries for generated-project evaluation."""

from __future__ import annotations

import json
from pathlib import Path


def target_groups(paths: tuple[Path, ...]) -> tuple[tuple[Path, ...], ...]:
    """Keep a Bun workspace's make targets and cleanup in one serial task."""
    groups: dict[Path, list[Path]] = {}
    for path in paths:
        owner = _bun_workspace(path) or path.resolve()
        groups.setdefault(owner, []).append(path)
    return tuple(tuple(group) for group in groups.values())


def _bun_workspace(path: Path) -> Path | None:
    if not (path / "package.json").is_file():
        return None
    resolved = path.resolve()
    for candidate in (path, *path.parents):
        patterns = _workspace_patterns(candidate)
        if not patterns:
            continue
        if resolved == candidate.resolve():
            return candidate.resolve()
        for pattern in patterns:
            if not pattern or Path(pattern).is_absolute():
                continue
            if any(member.resolve() == resolved for member in candidate.glob(pattern)):
                return candidate.resolve()
    return None


def _workspace_patterns(path: Path) -> tuple[str, ...]:
    try:
        package = json.loads((path / "package.json").read_text())
    except (OSError, ValueError):
        return ()
    if not isinstance(package, dict):
        return ()
    manager = package.get("packageManager", "")
    if not isinstance(manager, str) or not manager.startswith("bun@"):
        return ()
    workspaces = package.get("workspaces", [])
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages", [])
    if not isinstance(workspaces, list):
        return ()
    return tuple(pattern for pattern in workspaces if isinstance(pattern, str))
