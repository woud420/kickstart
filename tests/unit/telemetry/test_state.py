import json
import os
import stat
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from src.model.dto.telemetry import TelemetryConsent
from src.telemetry import state as state_module
from src.telemetry.state import TelemetryStateStore, default_telemetry_state_path
from src.utils.errors import TelemetryStateError


def test_default_path_honors_absolute_xdg_config_home(tmp_path: Path) -> None:
    assert default_telemetry_state_path({"XDG_CONFIG_HOME": str(tmp_path)}) == (
        tmp_path / "kickstart" / "telemetry.json"
    )


def test_default_path_ignores_relative_xdg_config_home(tmp_path: Path) -> None:
    assert default_telemetry_state_path({"XDG_CONFIG_HOME": "relative"}, home=tmp_path) == (
        tmp_path / ".config" / "kickstart" / "telemetry.json"
    )


def test_reading_missing_state_is_lazy(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")

    state = store.read()

    assert state.consent is TelemetryConsent.UNSET
    assert state.anonymous_id is None
    assert not store.path.exists()


def test_enable_creates_uuid4_and_reuses_it_across_store_instances(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.json"

    first = TelemetryStateStore(path).enable()
    second = TelemetryStateStore(path).enable()

    assert first.anonymous_id is not None
    assert first.anonymous_id.version == 4
    assert second.anonymous_id == first.anonymous_id
    assert second.consent is TelemetryConsent.ENABLED


def test_disable_before_enable_does_not_create_identity(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")

    state = store.disable()

    assert state.consent is TelemetryConsent.DISABLED
    assert state.anonymous_id is None
    assert "anonymous_id" not in json.loads(store.path.read_text(encoding="utf-8"))


def test_disable_and_reenable_preserve_identity(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    enabled = store.enable()

    disabled = store.disable()
    reenabled = store.enable()

    assert disabled.anonymous_id == enabled.anonymous_id
    assert reenabled.anonymous_id == enabled.anonymous_id


def test_reset_rotates_existing_identity_and_preserves_consent(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")
    original = store.enable()

    reset = store.reset_id()
    persisted = store.read()

    assert reset.previous_id == original.anonymous_id
    assert reset.current_id is not None
    assert reset.current_id != original.anonymous_id
    assert persisted.anonymous_id == reset.current_id
    assert persisted.consent is TelemetryConsent.ENABLED


def test_reset_without_identity_is_read_only(tmp_path: Path) -> None:
    store = TelemetryStateStore(tmp_path / "telemetry.json")

    reset = store.reset_id()

    assert reset.previous_id is None
    assert reset.current_id is None
    assert not store.path.exists()


def test_concurrent_enablement_converges_on_one_identity(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.json"
    candidates = iter([uuid4(), uuid4()])

    def enable() -> UUID | None:
        return TelemetryStateStore(path, uuid_factory=lambda: next(candidates)).enable().anonymous_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        identities = list(executor.map(lambda _: enable(), range(2)))

    assert identities[0] == identities[1]


@pytest.mark.skipif(not hasattr(stat, "S_IRUSR"), reason="permission bits unavailable")
def test_state_file_uses_user_only_permissions(tmp_path: Path) -> None:
    path = tmp_path / "kickstart" / "telemetry.json"

    TelemetryStateStore(path).enable()

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


def test_state_write_succeeds_when_descriptor_chmod_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delattr(state_module.os, "fchmod", raising=False)

    state = TelemetryStateStore(tmp_path / "telemetry.json").enable()

    assert state.consent is TelemetryConsent.ENABLED


def test_stale_lock_is_removed_before_updating_state(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.json"
    lock_path = tmp_path / ".telemetry.json.lock"
    lock_path.mkdir()
    os.utime(lock_path, (0, 0))

    state = TelemetryStateStore(path).disable()

    assert state.consent is TelemetryConsent.DISABLED
    assert not lock_path.exists()


def test_busy_lock_fails_without_changing_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "telemetry.json"
    lock_path = tmp_path / ".telemetry.json.lock"
    lock_path.mkdir()
    monkeypatch.setattr(state_module, "_LOCK_TIMEOUT_SECONDS", 0.0)

    with pytest.raises(TelemetryStateError, match="Telemetry state is busy"):
        TelemetryStateStore(path).enable()

    assert not path.exists()


def test_write_failure_removes_temporary_state_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "telemetry.json"

    def fail_replace(_source: Path, _destination: Path) -> None:
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(state_module.os, "replace", fail_replace)

    with pytest.raises(TelemetryStateError, match="cannot be written"):
        TelemetryStateStore(path).enable()

    assert list(tmp_path.glob(".telemetry-*.tmp")) == []


@pytest.mark.parametrize(
    "document",
    [
        [],
        {},
        {"schema_version": 2, "consent": "enabled", "anonymous_id": str(uuid4())},
        {"schema_version": 1, "consent": "enabled"},
        {"schema_version": 1, "consent": 1},
        {"schema_version": 1, "consent": "unset"},
        {"schema_version": 1, "consent": "enabled", "anonymous_id": "not-a-uuid"},
        {"schema_version": 1, "consent": "disabled", "anonymous_id": 1},
        {"schema_version": 1, "consent": "disabled", "anonymous_id": str(UUID(int=0, version=1))},
        {"schema_version": 1, "consent": "enabled", "anonymous_id": str(uuid4()), "extra": True},
    ],
)
def test_malformed_or_unknown_state_is_rejected(tmp_path: Path, document: object) -> None:
    path = tmp_path / "telemetry.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(TelemetryStateError):
        TelemetryStateStore(path).read()
