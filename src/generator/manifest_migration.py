"""Read-only manifest plans and explicit, guarded manifest-only application."""

from dataclasses import dataclass, field
import difflib
from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Literal

from src.generator.migration_inputs import MigrationDiagnostic, resolve_migration_inputs
from src.generator.scaffold_contract import MANIFEST_PATH, ScaffoldContract
from src.utils.errors import ManifestMigrationError, ManifestShapeError


@dataclass(frozen=True)
class MigrationPlan:
    root: Path
    source_version: str
    source_identity: tuple[int, int, int, int]
    source_bytes: bytes = field(repr=False)
    target_json: str | None = field(repr=False)
    diagnostics: tuple[MigrationDiagnostic, ...] = ()

    @property
    def ready(self) -> bool:
        return self.target_json is not None and not any(d.blocking for d in self.diagnostics)

    @property
    def diff(self) -> str:
        source = self.source_bytes.decode("utf-8", errors="replace")
        return "".join(
            difflib.unified_diff(
                source.splitlines(keepends=True),
                (self.target_json or source).splitlines(keepends=True),
                fromfile=MANIFEST_PATH,
                tofile=MANIFEST_PATH + " (4.0)",
            )
        )

    @property
    def source_sha256(self) -> str:
        return hashlib.sha256(self.source_bytes).hexdigest()

    def to_json(self, action: str = "planned") -> str:
        return (
            json.dumps(
                {
                    "root": str(self.root),
                    "source_version": self.source_version,
                    "target_version": "4.0",
                    "ready": self.ready,
                    "action": action,
                    "source_sha256": self.source_sha256,
                    "diff": self.diff,
                    "diagnostics": [
                        {"path": d.path, "code": d.code, "message": d.message, "blocking": d.blocking}
                        for d in self.diagnostics
                    ],
                },
                indent=2,
            )
            + "\n"
        )


def _identity(path: Path) -> tuple[int, int, int, int]:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ManifestMigrationError("migration requires a regular manifest file; symlinks are refused")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _manifest_path(root: Path) -> Path:
    if not root.is_dir() or root.resolve() != root:
        raise ManifestMigrationError(f"migration target '{root}' is not the original existing directory")
    if (root / ".kickstart").is_symlink():
        raise ManifestMigrationError("migration refuses a symlinked .kickstart directory")
    return root / MANIFEST_PATH


def plan_migration(root: Path, *, language: str | None = None, framework: str | None = None) -> MigrationPlan:
    if not root.is_dir():
        raise ManifestMigrationError(f"migration target '{root}' is not an existing directory")
    resolved = root.resolve()
    path = _manifest_path(resolved)
    try:
        identity = _identity(path)
        original = path.read_bytes()
        if _identity(path) != identity:
            raise ManifestMigrationError("manifest changed while planning; make a new plan")
    except OSError as error:
        raise ManifestMigrationError(f"cannot read migration manifest: {error}") from error
    source_version = "unknown"
    target = None
    diagnostics: tuple[MigrationDiagnostic, ...] = ()
    try:
        source = json.loads(original.decode("utf-8"))
        if not isinstance(source, dict):
            raise ManifestShapeError("manifest is not a JSON object")
        value = source.get("schema_version")
        source_version = value if isinstance(value, str) else "unknown"
        contract, diagnostics = resolve_migration_inputs(source, language, framework)
        if not any(d.blocking for d in diagnostics):
            target = contract.manifest_json(source["project"]["name"])
            if source_version == "4.0":
                target = original.decode("utf-8")
    except (ManifestShapeError, json.JSONDecodeError, UnicodeDecodeError) as error:
        diagnostics = (MigrationDiagnostic(MANIFEST_PATH, "invalid-manifest", str(error)),)
    return MigrationPlan(resolved, source_version, identity, original, target, diagnostics)


def apply_migration(plan: MigrationPlan, *, expected_sha256: str | None = None) -> Literal["applied", "unchanged"]:
    """Apply only the reviewed manifest, checking its snapshot before replacement."""
    if not plan.ready or plan.target_json is None:
        raise ManifestMigrationError("migration plan has unresolved or invalid inputs; no file was changed")
    if expected_sha256 is not None and expected_sha256 != plan.source_sha256:
        raise ManifestMigrationError("manifest differs from the expected reviewed SHA-256; make a new plan")
    try:
        payload = json.loads(plan.target_json)
        if not isinstance(payload, dict) or payload.get("schema_version") != "4.0":
            raise ManifestShapeError("migration target must be a schema-4 object")
        ScaffoldContract.from_manifest(payload)
    except (ManifestShapeError, json.JSONDecodeError) as error:
        raise ManifestMigrationError(f"invalid migration target: {error}") from error
    path = _manifest_path(plan.root)
    target = plan.target_json.encode("utf-8")
    temporary: Path | None = None
    try:
        identity = _identity(path)
        current = path.read_bytes()
        if current == target:
            return "unchanged"
        if identity != plan.source_identity or current != plan.source_bytes:
            raise ManifestMigrationError("manifest changed since planning; make a new plan")
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".scaffold-migrate-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(target)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        if _identity(path) != plan.source_identity or path.read_bytes() != plan.source_bytes:
            raise ManifestMigrationError("manifest changed since planning; make a new plan")
        os.replace(temporary, path)
    except OSError as error:
        raise ManifestMigrationError(f"cannot apply manifest migration: {error}") from error
    finally:
        if temporary is not None:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
    return "applied"
