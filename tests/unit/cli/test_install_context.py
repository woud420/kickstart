"""Install path resolution and shared failure policy."""

from pathlib import Path

import pytest
import typer


from tests.unit.cli.command_helpers import CONTEXT, InstallContext, report_failure, resolve_context

from src.utils.errors import KickstartError


def test_resolve_context_defaults_to_xdg(tmp_path, monkeypatch):
    """When --target is omitted the resolved install_dir falls back to ~/.local/bin."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setattr(CONTEXT, "path_contains", lambda *_args, **_kw: False)
    ctx = resolve_context(target=None, shell=None, rc_file=None)
    # The default install_dir module-level constant is computed at import time, so we just
    # assert the structural invariants instead of comparing against the live HOME.
    assert ctx.install_dir.name == "bin"
    assert ctx.shell == "zsh"
    assert ctx.rc_file is not None
    assert ctx.rc_file.name == ".zshrc"
    assert ctx.snippet.startswith("export PATH=")
    assert ctx.already_on_path is False


def test_resolve_context_honors_explicit_overrides(tmp_path):
    """Explicit --target / --rc-file / --shell win over detection."""
    target = tmp_path / "custom-bin"
    rc = tmp_path / "rc"
    ctx = resolve_context(target=target, shell="fish", rc_file=rc)
    assert ctx.install_dir == target
    assert ctx.shell == "fish"
    assert ctx.rc_file == rc
    assert ctx.snippet == f"fish_add_path -gp {target}"


def test_resolve_context_expands_user_paths(tmp_path, monkeypatch):
    """Tilde-prefixed paths should be expanded against HOME for both --target and --rc-file."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    ctx = resolve_context(
        target=Path("~/bin"),
        shell=None,
        rc_file=Path("~/.zshrc-override"),
    )
    assert ctx.install_dir == tmp_path / "bin"
    assert ctx.rc_file == tmp_path / ".zshrc-override"


def test_report_failure_converts_kickstart_error(capsys):
    """A KickstartError inside the helper exits non-zero with a uniform red banner."""
    with pytest.raises(typer.Exit) as excinfo:
        with report_failure("Install"):
            raise KickstartError("nope")
    assert excinfo.value.exit_code == 1
    out = capsys.readouterr().out
    assert "Install failed: nope" in out


def test_report_failure_converts_file_not_found(capsys):
    """FileNotFoundError is caught and reported under the same banner."""
    with pytest.raises(typer.Exit):
        with report_failure("Uninstall"):
            raise FileNotFoundError("missing")
    out = capsys.readouterr().out
    assert "Uninstall failed: missing" in out


def test_report_failure_lets_other_exceptions_through():
    """Exceptions we don't recognize should not be silently swallowed."""
    with pytest.raises(RuntimeError):
        with report_failure("Install"):
            raise RuntimeError("not handled")


def test_install_context_dataclass_is_frozen():
    """InstallContext should be immutable so commands can't mutate shared state."""
    ctx = InstallContext(
        install_dir=Path("/tmp/x"),
        app_root=Path("/tmp/x-app"),
        shell="zsh",
        rc_file=Path("/tmp/rc"),
        snippet='export PATH="/tmp/x:$PATH"',
        already_on_path=False,
    )
    with pytest.raises(Exception):
        ctx.install_dir = Path("/tmp/y")  # type: ignore[misc]
