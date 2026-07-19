"""Durable user-scoped telemetry consent and identity state."""

import json
import os
import tempfile
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TypeAlias, cast
from uuid import UUID, uuid4

from src.model.dto.telemetry import (
    TELEMETRY_STATE_SCHEMA_VERSION,
    TelemetryConsent,
    TelemetryIdentityReset,
    TelemetryState,
    TelemetryStateDocument,
)
from src.utils.errors import TelemetryStateError


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
_LOCK_TIMEOUT_SECONDS = 1.0
_STALE_LOCK_SECONDS = 30.0


def default_telemetry_state_path(
    environ: Mapping[str, str] | None = None,
    *,
    home: Path | None = None,
) -> Path:
    """Return a user-scoped path that survives application upgrades."""
    process_environment = os.environ if environ is None else environ
    xdg_value = process_environment.get("XDG_CONFIG_HOME")
    if xdg_value:
        xdg_path = Path(xdg_value).expanduser()
        if xdg_path.is_absolute():
            return xdg_path / "kickstart" / "telemetry.json"
    home_path = Path.home() if home is None else home
    return home_path.expanduser() / ".config" / "kickstart" / "telemetry.json"


class TelemetryStateStore:
    """Read and atomically update versioned telemetry state."""

    def __init__(self, path: Path, *, uuid_factory: Callable[[], UUID] = uuid4) -> None:
        self.path = path
        self._uuid_factory = uuid_factory

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> "TelemetryStateStore":
        """Construct the default store without consulting project configuration."""
        return cls(default_telemetry_state_path(environ))

    def read(self) -> TelemetryState:
        """Read state without creating a file; missing state means not opted in."""
        if not self.path.exists():
            return TelemetryState()
        try:
            payload = cast(JsonValue, json.loads(self.path.read_text(encoding="utf-8")))
            return _parse_state(payload)
        except (OSError, TypeError, ValueError) as exc:
            raise TelemetryStateError("Telemetry state is unreadable or malformed; telemetry is disabled.") from exc

    def enable(self) -> TelemetryState:
        """Persist opt-in and lazily create a stable UUIDv4 identity."""
        with self._locked():
            current = self.read()
            anonymous_id = current.anonymous_id or self._uuid_factory()
            state = TelemetryState(consent=TelemetryConsent.ENABLED, anonymous_id=anonymous_id)
            self._write(state)
            return state

    def disable(self) -> TelemetryState:
        """Persist opt-out while retaining any existing identity."""
        with self._locked():
            current = self.read()
            state = TelemetryState(consent=TelemetryConsent.DISABLED, anonymous_id=current.anonymous_id)
            self._write(state)
            return state

    def reset_id(self) -> TelemetryIdentityReset:
        """Rotate an existing identity without changing consent."""
        with self._locked():
            current = self.read()
            if current.anonymous_id is None:
                return TelemetryIdentityReset(previous_id=None, current_id=None)
            new_id = self._uuid_factory()
            self._write(TelemetryState(consent=current.consent, anonymous_id=new_id))
            return TelemetryIdentityReset(previous_id=current.anonymous_id, current_id=new_id)

    @contextmanager
    def _locked(self) -> Iterator[None]:
        """Serialize updates with a small, cross-platform directory lock."""
        self._ensure_parent()
        lock_path = self.path.with_name(f".{self.path.name}.lock")
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        while True:
            try:
                lock_path.mkdir(mode=0o700)
                break
            except FileExistsError as exc:
                if _remove_stale_lock(lock_path):
                    continue
                if time.monotonic() >= deadline:
                    raise TelemetryStateError("Telemetry state is busy; no preference was changed.") from exc
                time.sleep(0.01)
            except OSError as exc:
                raise TelemetryStateError("Telemetry state cannot be locked; no preference was changed.") from exc
        try:
            yield
        finally:
            try:
                lock_path.rmdir()
            except OSError:
                pass

    def _ensure_parent(self) -> None:
        try:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            self.path.parent.chmod(0o700)
        except OSError as exc:
            raise TelemetryStateError("Telemetry state directory cannot be created; telemetry is disabled.") from exc

    def _write(self, state: TelemetryState) -> None:
        document: TelemetryStateDocument = {
            "schema_version": state.schema_version,
            "consent": state.consent.value,
        }
        if state.anonymous_id is not None:
            document["anonymous_id"] = str(state.anonymous_id)

        temporary_path: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(prefix=".telemetry-", suffix=".tmp", dir=self.path.parent)
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                if hasattr(os, "fchmod"):
                    os.fchmod(handle.fileno(), 0o600)
                handle.write(json.dumps(document, indent=2, sort_keys=True))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            self.path.chmod(0o600)
        except OSError as exc:
            raise TelemetryStateError("Telemetry state cannot be written; telemetry is disabled.") from exc
        finally:
            if temporary_path is not None and temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass


def _parse_state(payload: JsonValue) -> TelemetryState:
    if not isinstance(payload, dict):
        raise ValueError("state must be an object")
    allowed_keys = {"schema_version", "consent", "anonymous_id"}
    if set(payload) - allowed_keys:
        raise ValueError("state contains unknown fields")
    if payload.get("schema_version") != TELEMETRY_STATE_SCHEMA_VERSION:
        raise ValueError("unsupported state schema")

    consent_value = payload.get("consent")
    if not isinstance(consent_value, str):
        raise ValueError("consent must be a string")
    consent = TelemetryConsent(consent_value)
    if consent is TelemetryConsent.UNSET:
        raise ValueError("unset consent is not persisted")

    identity_value = payload.get("anonymous_id")
    anonymous_id: UUID | None = None
    if identity_value is not None:
        if not isinstance(identity_value, str):
            raise ValueError("anonymous_id must be a string")
        anonymous_id = UUID(identity_value)
        if anonymous_id.version != 4:
            raise ValueError("anonymous_id must be UUIDv4")
    if consent is TelemetryConsent.ENABLED and anonymous_id is None:
        raise ValueError("enabled telemetry requires an identity")
    return TelemetryState(consent=consent, anonymous_id=anonymous_id)


def _remove_stale_lock(lock_path: Path) -> bool:
    try:
        if time.time() - lock_path.stat().st_mtime <= _STALE_LOCK_SECONDS:
            return False
        lock_path.rmdir()
        return True
    except OSError:
        return False
