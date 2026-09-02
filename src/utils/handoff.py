"""Activate a staged kickstart payload from outside the managed app root.

Replacing ``<app_root>/current`` from a process that executes inside it removes
the running PyInstaller payload underneath that process: the swap succeeds, but
the process can no longer load its own modules and exits non-zero. Every
managed onedir activation therefore runs as a chain of process handoffs:

1. ``kickstart upgrade`` (wherever it runs) stages the payload to activate under
   the operating-system temporary directory, records a handoff manifest next to
   it, and replaces itself with the staged launcher (``os.execve``).
2. The staged process runs outside the app root, so it can use the
   rollback-safe installer to replace ``<app_root>/current``. It verifies the
   public launcher and replaces itself with the freshly activated canonical
   launcher.
3. The canonical process removes the staging directory and reports the
   terminal result. Its own successful start proves the activated payload runs.

A hop either replaces itself or terminates, and only a terminating hop reports
telemetry, so exactly one ``cli_upgrade_completed`` event is attempted per
``kickstart upgrade`` invocation.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping, NoReturn, Optional

from rich import print

from src.model.dto.telemetry import (
    CliUpgradeChecksumStatus,
    CliUpgradeErrorCategory,
    CliUpgradeOutcome,
)
from src.model.dto.upgrade import UNKNOWN_TARGET_VERSION, UpgradeResult
from src.utils.errors import HandoffError
from src.utils.installer import (
    APP_DIR_NAME,
    BINARY_NAME,
    InstallResult,
    _onedir_bundle_root,
    _safe_resolve,
    current_binary_path,
    install_binary,
)


HANDOFF_VERSION: int = 1
HANDOFF_FILENAME: str = "handoff.json"
HANDOFF_COMMAND: str = "managed-layout-handoff"
STAGE_PREFIX_REPAIR: str = "kickstart-repair-"
STAGE_PREFIX_UPGRADE: str = "kickstart-upgrade-"

# Environment the PyInstaller bootloader sets for its own process. Inheriting
# it would make the staged bootloader resolve libraries from the payload we
# are about to replace, so every handoff scrubs it.
_BOOTLOADER_ENV_PREFIXES: tuple[str, ...] = ("_PYI_", "_MEIPASS")
_LIBRARY_PATH_VARS: tuple[str, ...] = ("LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH")


class HandoffMode(StrEnum):
    """Why a payload is being activated through a handoff."""

    REPAIR = "repair"
    UPGRADE = "upgrade"


class HandoffPhase(StrEnum):
    """Which hop of the handoff chain a process is executing."""

    ACTIVATE = "activate"
    FINALIZE = "finalize"


@dataclass(frozen=True)
class Handoff:
    """Everything a later hop needs to finish an activation and report it."""

    mode: HandoffMode
    launcher_dir: Path
    app_root: Path
    bundle_launcher: Path
    target_version: str
    checksum_status: CliUpgradeChecksumStatus
    started_at: float

    @property
    def canonical_launcher(self) -> Path:
        """Return the executable every public launcher must resolve to after activation."""
        return self.app_root / APP_DIR_NAME / BINARY_NAME

    @property
    def public_launcher(self) -> Path:
        """Return the launcher path users invoke."""
        return self.launcher_dir / BINARY_NAME

    def success(self) -> UpgradeResult:
        """Return the terminal result for a completed activation."""
        outcome = CliUpgradeOutcome.REPAIRED if self.mode is HandoffMode.REPAIR else CliUpgradeOutcome.UPDATED
        return UpgradeResult(
            target_version=self.target_version,
            outcome=outcome,
            error_category=CliUpgradeErrorCategory.NONE,
            checksum_status=self.checksum_status,
        )

    def failure(self, error_category: CliUpgradeErrorCategory) -> UpgradeResult:
        """Return the terminal result for an activation that did not complete."""
        return UpgradeResult(
            target_version=self.target_version,
            outcome=CliUpgradeOutcome.FAILED,
            error_category=error_category,
            checksum_status=self.checksum_status,
        )

    def write(self, stage_dir: Path) -> Path:
        """Persist the manifest inside `stage_dir` and return its path."""
        payload = {
            "version": HANDOFF_VERSION,
            "mode": self.mode.value,
            "launcher_dir": str(self.launcher_dir),
            "app_root": str(self.app_root),
            "bundle_launcher": str(self.bundle_launcher),
            "target_version": self.target_version,
            "checksum_status": self.checksum_status.value,
            "started_at": self.started_at,
        }
        manifest = stage_dir / HANDOFF_FILENAME
        manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return manifest


def unknown_failure(error_category: CliUpgradeErrorCategory) -> UpgradeResult:
    """Return a terminal failure for a hop that could not even read its manifest."""
    return UpgradeResult(
        target_version=UNKNOWN_TARGET_VERSION,
        outcome=CliUpgradeOutcome.FAILED,
        error_category=error_category,
        checksum_status=CliUpgradeChecksumStatus.NOT_REACHED,
    )


def load_handoff(stage_dir: Path) -> Handoff:
    """Read the manifest a previous hop wrote into `stage_dir`."""
    manifest = stage_dir / HANDOFF_FILENAME
    try:
        raw = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HandoffError(f"cannot read handoff manifest {manifest}: {exc}") from exc
    if not isinstance(raw, dict):
        raise HandoffError(f"handoff manifest {manifest} is not an object")
    version = raw.get("version")
    if version != HANDOFF_VERSION:
        raise HandoffError(f"unsupported handoff manifest version {version!r} in {manifest}")
    try:
        return Handoff(
            mode=HandoffMode(str(raw["mode"])),
            launcher_dir=Path(str(raw["launcher_dir"])),
            app_root=Path(str(raw["app_root"])),
            bundle_launcher=Path(str(raw["bundle_launcher"])),
            target_version=str(raw["target_version"]),
            checksum_status=CliUpgradeChecksumStatus(str(raw["checksum_status"])),
            started_at=float(raw["started_at"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HandoffError(f"handoff manifest {manifest} is malformed: {exc}") from exc


def create_stage_dir(mode: HandoffMode) -> Path:
    """Create the staging directory for `mode` under the OS temporary directory."""
    prefix = STAGE_PREFIX_REPAIR if mode is HandoffMode.REPAIR else STAGE_PREFIX_UPGRADE
    return Path(tempfile.mkdtemp(prefix=prefix))


def running_bundle_root() -> Optional[Path]:
    """Return the onedir payload directory the current process executes from, if any."""
    return _onedir_bundle_root(current_binary_path())


def stage_running_bundle(stage_dir: Path) -> Path:
    """Copy the running onedir payload into `stage_dir` and return the staged launcher."""
    bundle_root = running_bundle_root()
    if bundle_root is None:
        raise HandoffError("the running executable is not a kickstart onedir payload; nothing to stage")
    staged_root = stage_dir / bundle_root.name
    shutil.copytree(bundle_root, staged_root, symlinks=True)
    return staged_root / BINARY_NAME


def handoff_environment(
    env: Optional[Mapping[str, str]] = None,
    bundle_root: Optional[Path] = None,
) -> dict[str, str]:
    """Return a child environment without the running bootloader's private state.

    Follows PyInstaller's guidance for launching other executables from a
    frozen process: drop the bootloader's own variables and restore the
    library search path it saved (or strip the entries that point into the
    running payload when no saved value exists).
    """
    source = os.environ if env is None else env
    child = {key: value for key, value in source.items() if not key.startswith(_BOOTLOADER_ENV_PREFIXES)}
    payload_root = _safe_resolve(bundle_root) if bundle_root is not None else None
    for variable in _LIBRARY_PATH_VARS:
        saved = child.pop(f"{variable}_ORIG", None)
        if saved is not None:
            if saved:
                child[variable] = saved
            else:
                child.pop(variable, None)
            continue
        current = child.get(variable)
        if current is None or payload_root is None:
            continue
        kept = [
            entry
            for entry in current.split(os.pathsep)
            if entry and not _safe_resolve(Path(entry)).is_relative_to(payload_root)
        ]
        if kept:
            child[variable] = os.pathsep.join(kept)
        else:
            child.pop(variable, None)
    return child


def exec_launcher(launcher: Path, args: list[str], env: dict[str, str]) -> NoReturn:
    """Replace the current process with `launcher`. Raises OSError when that is impossible."""
    sys.stdout.flush()
    sys.stderr.flush()
    os.execve(str(launcher), [str(launcher), *args], env)


def _phase_args(stage_dir: Path, phase: HandoffPhase) -> list[str]:
    return [HANDOFF_COMMAND, "--stage-dir", str(stage_dir), "--phase", phase.value]


def handoff_to_staged(handoff: Handoff, stage_dir: Path) -> NoReturn:
    """Write the manifest and replace this process with the staged launcher."""
    handoff.write(stage_dir)
    env = handoff_environment(bundle_root=running_bundle_root())
    exec_launcher(handoff.bundle_launcher, _phase_args(stage_dir, HandoffPhase.ACTIVATE), env)


def activate(handoff: Handoff, stage_dir: Path) -> UpgradeResult:
    """Activate the staged payload, verify the launcher, and hand off to the canonical binary.

    Runs in the staged process. Returns only when the activated payload is in
    place but the final handoff could not be executed; the caller then reports
    the successful result itself and leaves `stage_dir` for manual removal.
    Every exception means the installer already rolled the previous payload back.
    """
    if _safe_resolve(handoff.bundle_launcher).is_relative_to(_safe_resolve(handoff.app_root)):
        raise HandoffError(
            f"staged payload {handoff.bundle_launcher} lives inside the managed app root {handoff.app_root}"
        )
    print(f"[cyan]Activating {handoff.mode.value} payload from staging...")
    result: InstallResult = install_binary(
        handoff.bundle_launcher,
        target_dir=handoff.launcher_dir,
        overwrite=True,
        app_root=handoff.app_root,
    )
    verify_activated_layout(handoff)
    print(f"  launcher: {result.destination}")
    if result.app_path is not None:
        print(f"  app:      {result.app_path}")
    env = handoff_environment(bundle_root=running_bundle_root())
    try:
        exec_launcher(handoff.canonical_launcher, _phase_args(stage_dir, HandoffPhase.FINALIZE), env)
    except OSError as exc:
        print(f"[yellow]⚠ Activated, but could not start the new launcher to clean up: {exc}")
        print(f"  Remove the staging directory manually: {stage_dir}")
        return handoff.success()


def verify_activated_layout(handoff: Handoff) -> None:
    """Raise HandoffError unless the public launcher resolves exactly to the canonical payload."""
    expected = _safe_resolve(handoff.app_root / APP_DIR_NAME) / BINARY_NAME
    actual = _safe_resolve(handoff.public_launcher)
    if actual != expected:
        raise HandoffError(f"launcher {handoff.public_launcher} resolves to {actual}, expected {expected}")
    if not expected.is_file() or expected.is_symlink():
        raise HandoffError(f"canonical payload executable {expected} is missing or is not a regular file")
    nested = handoff.app_root / APP_DIR_NAME / f".{BINARY_NAME}"
    if nested.exists() or nested.is_symlink():
        raise HandoffError(f"nested payload directory {nested} survived activation")


def finalize(handoff: Handoff, stage_dir: Path) -> UpgradeResult:
    """Remove the staging directory and return the terminal result. Runs in the canonical process."""
    shutil.rmtree(stage_dir, ignore_errors=True)
    if handoff.mode is HandoffMode.REPAIR:
        print(f"[green]✔ Repaired the managed install layout (version {handoff.target_version}).")
    else:
        print(f"[green]✔ Updated to {handoff.target_version}.")
    print(f"  launcher: {handoff.public_launcher}")
    print(f"  app:      {handoff.app_root / APP_DIR_NAME}")
    return handoff.success()
