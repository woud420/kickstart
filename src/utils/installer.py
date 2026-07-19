"""Install the kickstart binary into a user-writable location and help configure PATH.

This module is intentionally self-contained so that the `install` CLI command works
when kickstart is executed from a PyInstaller-built binary (single-file or onedir),
from a Poetry virtualenv, or from a regular Python entry-point script.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_INSTALL_DIR: Path = Path.home() / ".local" / "bin"
DEFAULT_APP_ROOT: Path = Path.home() / ".local" / "share" / "kickstart"
BINARY_NAME: str = "kickstart"
APP_DIR_NAME: str = "current"

MARKER_BEGIN: str = "# >>> kickstart install >>>"
MARKER_END: str = "# <<< kickstart install <<<"

EXECUTABLE_BITS: int = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

# Conventional shell rc files. macOS interactive bash reads ~/.bash_profile, so we
# pick that when the platform is darwin and fall back to ~/.bashrc elsewhere.
_SHELL_RC_LAYOUT: dict[str, tuple[str, ...]] = {
    "zsh": (".zshrc",),
    "bash-darwin": (".bash_profile",),
    "bash": (".bashrc",),
    "fish": (".config", "fish", "config.fish"),
}

_MANAGED_BLOCK_RE: re.Pattern[str] = re.compile(
    rf"{re.escape(MARKER_BEGIN)}.*?{re.escape(MARKER_END)}\n?",
    re.DOTALL,
)


@dataclass(frozen=True)
class InstallResult:
    """Outcome of an install attempt."""

    source: Path
    destination: Path
    copied: bool
    already_installed: bool
    app_root: Optional[Path] = None
    app_path: Optional[Path] = None


@dataclass(frozen=True)
class PathUpdateResult:
    """Outcome of a shell rc file PATH update attempt."""

    rc_file: Path
    snippet: str
    changed: bool
    on_path_now: bool


def current_entrypoint_path() -> Path:
    """Return the absolute invocation path without resolving symlinks.

    Preserving the logical path matters for managed installs: the launcher
    symlink identifies both its public directory and the managed app root. A
    bare command name is resolved through ``PATH`` so callers still receive an
    absolute path.
    """
    raw_argv0 = sys.argv[0] if sys.argv and sys.argv[0] else None
    if raw_argv0 is not None:
        argv0 = Path(raw_argv0).expanduser()
        candidate = argv0
        is_bare_command = os.sep not in raw_argv0 and (os.altsep is None or os.altsep not in raw_argv0)
        if is_bare_command:
            located = shutil.which(str(argv0))
            if located is not None:
                candidate = Path(located)
        if candidate.exists() or candidate.is_symlink():
            return Path(os.path.abspath(candidate))
    return Path(os.path.abspath(sys.executable))


def current_binary_path() -> Path:
    """Return the resolved absolute path of the running kickstart executable.

    Tries `sys.argv[0]` first (correct for PyInstaller `--onefile` and `--onedir`
    builds and for console-script shims) and falls back to `sys.executable` when
    argv[0] does not point to a real file (this is what happens with `python -m`).
    """
    return _safe_resolve(current_entrypoint_path())


def detect_shell(env: Optional[dict[str, str]] = None) -> Optional[str]:
    """Return the shell name from $SHELL when it is one we know how to configure."""
    shell = _env(env).get("SHELL", "")
    if not shell:
        return None
    name = Path(shell).name.lower()
    if name in {"zsh", "bash", "fish"}:
        return name
    return None


def default_rc_for_shell(
    shell: Optional[str],
    home: Optional[Path] = None,
    platform: Optional[str] = None,
) -> Optional[Path]:
    """Pick the conventional rc file for a shell."""
    if shell == "bash":
        key = "bash-darwin" if (platform or sys.platform) == "darwin" else "bash"
    else:
        key = shell or ""
    parts = _SHELL_RC_LAYOUT.get(key)
    if parts is None:
        return None
    return (home if home is not None else Path.home()).joinpath(*parts)


def default_app_root(target_dir: Path = DEFAULT_INSTALL_DIR) -> Path:
    """Return where an onedir install should store the binary payload for `target_dir`."""
    expanded = target_dir.expanduser()
    if expanded.name == "bin":
        return expanded.parent / "share" / BINARY_NAME
    return expanded / f".{BINARY_NAME}"


def path_contains(target: Path, env: Optional[dict[str, str]] = None) -> bool:
    """Return True when `target` is already an entry of $PATH."""
    raw = _env(env).get("PATH", "")
    if not raw:
        return False
    resolved_target = _safe_resolve(target)
    for entry in raw.split(os.pathsep):
        if not entry:
            continue
        candidate = Path(entry)
        if candidate == target or _safe_resolve(candidate) == resolved_target:
            return True
    return False


def path_update_snippet(shell: Optional[str], target_dir: Path) -> str:
    """Return the line of shell to append to an rc file."""
    if shell == "fish":
        return f"fish_add_path -gp {target_dir}"
    return f'export PATH="{target_dir}:$PATH"'


def install_binary(
    source: Path,
    target_dir: Path = DEFAULT_INSTALL_DIR,
    name: str = BINARY_NAME,
    overwrite: bool = True,
    app_root: Optional[Path] = None,
) -> InstallResult:
    """Install `source` into `target_dir/name` with executable permissions.

    Single-file binaries are copied directly. PyInstaller onedir apps are copied
    as a directory payload and exposed through a symlink or tiny wrapper at
    `target_dir/name`.

    Raises FileNotFoundError when `source` does not exist, FileExistsError when
    the destination already exists and overwrite is False.
    """
    source = source.expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Source binary not found: {source}")

    bundle_source = _onedir_bundle_root(source, name=name)
    if bundle_source is not None:
        return _install_onedir_bundle(
            source=source,
            bundle_source=bundle_source,
            target_dir=target_dir,
            name=name,
            overwrite=overwrite,
            app_root=app_root,
        )

    return _install_single_file_binary(source, target_dir, name=name, overwrite=overwrite)


def _install_single_file_binary(
    source: Path,
    target_dir: Path,
    *,
    name: str,
    overwrite: bool,
) -> InstallResult:
    """Copy a one-file executable into the target directory."""
    target_dir = target_dir.expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / name

    if destination.exists():
        if _same_file(destination, source):
            return InstallResult(source=source, destination=destination, copied=False, already_installed=True)
        if not overwrite:
            raise FileExistsError(f"{destination} already exists; pass --force to overwrite")

    shutil.copy2(source, destination)
    destination.chmod(destination.stat().st_mode | EXECUTABLE_BITS)
    return InstallResult(source=source, destination=destination, copied=True, already_installed=False)


def _install_onedir_bundle(
    *,
    source: Path,
    bundle_source: Path,
    target_dir: Path,
    name: str,
    overwrite: bool,
    app_root: Optional[Path],
) -> InstallResult:
    """Install a PyInstaller onedir app and expose it through `target_dir/name`."""
    target_dir = target_dir.expanduser()
    resolved_app_root = (app_root or default_app_root(target_dir)).expanduser()
    bundle_destination = resolved_app_root / APP_DIR_NAME
    executable_destination = bundle_destination / name
    destination = target_dir / name

    target_dir.mkdir(parents=True, exist_ok=True)
    resolved_app_root.mkdir(parents=True, exist_ok=True)

    copied = False
    if not _same_file(bundle_source, bundle_destination):
        if (bundle_destination.exists() or bundle_destination.is_symlink()) and not overwrite:
            raise FileExistsError(f"{bundle_destination} already exists; pass --force to overwrite")
        _replace_bundle(bundle_source, bundle_destination)
        copied = True

    launcher_changed = _install_launcher(executable_destination, destination, overwrite=overwrite)
    return InstallResult(
        source=source,
        destination=destination,
        copied=copied or launcher_changed,
        already_installed=not copied and not launcher_changed,
        app_root=resolved_app_root,
        app_path=bundle_destination,
    )


def uninstall_binary(
    target_dir: Path = DEFAULT_INSTALL_DIR,
    name: str = BINARY_NAME,
    app_root: Optional[Path] = None,
) -> Optional[Path]:
    """Remove an installed kickstart launcher and onedir payload if present."""
    target_dir = target_dir.expanduser()
    destination = target_dir / name
    removed = None
    if destination.exists() or destination.is_symlink():
        _remove_path(destination)
        removed = destination

    resolved_app_root = (app_root or default_app_root(target_dir)).expanduser()
    if resolved_app_root.exists() or resolved_app_root.is_symlink():
        _remove_path(resolved_app_root)

    return removed


def update_path_in_rc(rc_path: Path, snippet: str) -> bool:
    """Append (or refresh) a managed PATH block in `rc_path`.

    Returns True when the file changed. Reuses a marker pair to keep at most one
    managed block per rc file, so re-running install is idempotent.
    """
    block = _format_managed_block(snippet)
    existing = rc_path.read_text() if rc_path.exists() else None

    if existing is None:
        rc_path.parent.mkdir(parents=True, exist_ok=True)
        rc_path.write_text(block)
        return True

    if MARKER_BEGIN in existing:
        current = _MANAGED_BLOCK_RE.search(existing)
        if current is not None and current.group(0).rstrip("\n") == block.rstrip("\n"):
            return False
        rc_path.write_text(_MANAGED_BLOCK_RE.sub(block, existing, count=1))
        return True

    separator = "" if existing == "" or existing.endswith("\n") else "\n"
    rc_path.write_text(existing + separator + block)
    return True


def remove_path_block_from_rc(rc_path: Path) -> bool:
    """Remove the managed PATH block from `rc_path`. Returns True when the file changed."""
    if not rc_path.exists():
        return False
    existing = rc_path.read_text()
    if MARKER_BEGIN not in existing:
        return False
    cleanup_re = re.compile(rf"\n?{_MANAGED_BLOCK_RE.pattern}", _MANAGED_BLOCK_RE.flags)
    rc_path.write_text(cleanup_re.sub("\n", existing, count=1).lstrip("\n"))
    return True


def _format_managed_block(snippet: str) -> str:
    """Render the full ``MARKER_BEGIN / snippet / MARKER_END`` block, newline-terminated."""
    return "\n".join([MARKER_BEGIN, snippet, MARKER_END]) + "\n"


def _env(env: Optional[dict[str, str]]) -> dict[str, str] | os._Environ[str]:
    return env if env is not None else os.environ


def _safe_resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _same_file(a: Path, b: Path) -> bool:
    try:
        return _safe_resolve(a) == _safe_resolve(b)
    except OSError:
        return False


def _onedir_bundle_root(source: Path, *, name: str = BINARY_NAME) -> Optional[Path]:
    """Return the PyInstaller onedir root for `source`, if it looks like one."""
    candidates = [source, _safe_resolve(source)]
    for candidate in candidates:
        if candidate.name != name:
            continue
        root = candidate.parent
        if candidate.is_file() and (root / "_internal").is_dir():
            return root
    return None


def _replace_bundle(bundle_source: Path, bundle_destination: Path) -> None:
    """Stage and activate a bundle with rollback for staging or activation errors."""
    app_root = bundle_destination.parent
    suffix = os.getpid()
    temp_destination = app_root / f".{APP_DIR_NAME}.tmp-{suffix}"
    backup_destination = app_root / f".{APP_DIR_NAME}.backup-{suffix}"

    for path in (temp_destination, backup_destination):
        if path.exists() or path.is_symlink():
            _remove_path(path)

    try:
        shutil.copytree(bundle_source, temp_destination, symlinks=True)
    except Exception:
        if temp_destination.exists() or temp_destination.is_symlink():
            _remove_path(temp_destination)
        raise

    previous_moved = False
    try:
        if bundle_destination.exists() or bundle_destination.is_symlink():
            bundle_destination.rename(backup_destination)
            previous_moved = True
        try:
            temp_destination.rename(bundle_destination)
        except Exception:
            if previous_moved:
                backup_destination.rename(bundle_destination)
            raise
    finally:
        if temp_destination.exists() or temp_destination.is_symlink():
            _remove_path(temp_destination)

    if previous_moved:
        _remove_path(backup_destination)


def _install_launcher(executable: Path, destination: Path, *, overwrite: bool) -> bool:
    """Expose `executable` at `destination`, preferring a symlink."""
    if destination.exists() or destination.is_symlink():
        if _same_file(destination, executable):
            return False
        if not overwrite:
            raise FileExistsError(f"{destination} already exists; pass --force to overwrite")
        _remove_path(destination)

    try:
        destination.symlink_to(executable)
    except OSError:
        destination.write_text(f'#!/bin/sh\nexec "{executable}" "$@"\n')
        destination.chmod(destination.stat().st_mode | EXECUTABLE_BITS)
    return True


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
