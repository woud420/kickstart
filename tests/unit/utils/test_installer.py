"""Tests for src.utils.installer."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from src.utils import installer


@pytest.fixture()
def single_file_binary(tmp_path: Path) -> Path:
    source = tmp_path / "bin" / "kickstart-source"
    source.parent.mkdir(parents=True)
    source.write_text("#!/bin/sh\necho hi\n")
    source.chmod(0o755)
    return source


def test_install_binary_creates_destination(tmp_path: Path, single_file_binary: Path) -> None:
    target_dir = tmp_path / "user-bin"
    result = installer.install_binary(single_file_binary, target_dir)

    assert result.copied is True
    assert result.already_installed is False
    assert result.destination == target_dir / installer.BINARY_NAME
    assert result.destination.exists()

    mode = result.destination.stat().st_mode
    assert mode & stat.S_IXUSR
    assert mode & stat.S_IXGRP
    assert mode & stat.S_IXOTH


def test_install_binary_refuses_overwrite_without_force(tmp_path: Path, single_file_binary: Path) -> None:
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    (target_dir / installer.BINARY_NAME).write_text("placeholder")

    with pytest.raises(FileExistsError):
        installer.install_binary(single_file_binary, target_dir, overwrite=False)


def test_install_binary_overwrites_with_force(tmp_path: Path, single_file_binary: Path) -> None:
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    destination = target_dir / installer.BINARY_NAME
    destination.write_text("placeholder")

    result = installer.install_binary(single_file_binary, target_dir, overwrite=True)
    assert result.copied is True
    assert destination.read_text() == single_file_binary.read_text()


def test_install_binary_idempotent_when_same_file(tmp_path: Path, single_file_binary: Path) -> None:
    target_dir = single_file_binary.parent
    target = target_dir / installer.BINARY_NAME
    target.symlink_to(single_file_binary)
    result = installer.install_binary(single_file_binary, target_dir, name=installer.BINARY_NAME)
    assert result.already_installed is True
    assert result.copied is False


def test_install_binary_missing_source_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        installer.install_binary(missing, tmp_path / "bin")


def test_current_entrypoint_path_preserves_symlink_for_layout_discovery(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "app" / installer.BINARY_NAME
    target.parent.mkdir()
    target.write_text("#!/bin/sh\n")
    launcher = tmp_path / "bin" / installer.BINARY_NAME
    launcher.parent.mkdir()
    launcher.symlink_to(target)
    monkeypatch.setattr(installer.sys, "argv", [str(launcher)])

    assert installer.current_entrypoint_path() == launcher
    assert installer.current_binary_path() == target


def test_current_entrypoint_path_finds_bare_command_on_path(tmp_path: Path, monkeypatch) -> None:
    launcher = tmp_path / installer.BINARY_NAME
    launcher.write_text("#!/bin/sh\n")
    monkeypatch.setattr(installer.sys, "argv", [installer.BINARY_NAME])
    monkeypatch.setattr(installer.shutil, "which", lambda command: str(launcher))

    assert installer.current_entrypoint_path() == launcher


def test_current_entrypoint_path_preserves_explicit_relative_path(tmp_path: Path, monkeypatch) -> None:
    working_dir = tmp_path / "working"
    working_dir.mkdir()
    explicit_launcher = working_dir / installer.BINARY_NAME
    explicit_launcher.write_text("#!/bin/sh\n")
    path_launcher = tmp_path / "path-bin" / installer.BINARY_NAME
    path_launcher.parent.mkdir()
    path_launcher.write_text("#!/bin/sh\n")

    monkeypatch.chdir(working_dir)
    monkeypatch.setattr(installer.sys, "argv", [f".{os.sep}{installer.BINARY_NAME}"])
    monkeypatch.setattr(installer.shutil, "which", lambda command: str(path_launcher))

    assert installer.current_entrypoint_path() == explicit_launcher


def test_uninstall_binary_removes_file(tmp_path: Path, single_file_binary: Path) -> None:
    target_dir = tmp_path / "user-bin"
    installer.install_binary(single_file_binary, target_dir)
    removed = installer.uninstall_binary(target_dir)
    assert removed == target_dir / installer.BINARY_NAME
    assert not removed.exists()


def test_uninstall_binary_returns_none_when_absent(tmp_path: Path) -> None:
    assert installer.uninstall_binary(tmp_path) is None


def test_detect_shell_zsh() -> None:
    assert installer.detect_shell({"SHELL": "/bin/zsh"}) == "zsh"


def test_detect_shell_bash() -> None:
    assert installer.detect_shell({"SHELL": "/usr/local/bin/bash"}) == "bash"


def test_detect_shell_fish() -> None:
    assert installer.detect_shell({"SHELL": "/opt/homebrew/bin/fish"}) == "fish"


def test_detect_shell_unknown() -> None:
    assert installer.detect_shell({"SHELL": "/bin/tcsh"}) is None
    assert installer.detect_shell({}) is None


def test_default_rc_for_shell_zsh(tmp_path: Path) -> None:
    assert installer.default_rc_for_shell("zsh", home=tmp_path) == tmp_path / ".zshrc"


def test_default_rc_for_shell_bash_macos(tmp_path: Path) -> None:
    assert installer.default_rc_for_shell("bash", home=tmp_path, platform="darwin") == tmp_path / ".bash_profile"


def test_default_rc_for_shell_bash_linux(tmp_path: Path) -> None:
    assert installer.default_rc_for_shell("bash", home=tmp_path, platform="linux") == tmp_path / ".bashrc"


def test_default_rc_for_shell_fish(tmp_path: Path) -> None:
    assert installer.default_rc_for_shell("fish", home=tmp_path) == tmp_path / ".config" / "fish" / "config.fish"


def test_default_rc_for_shell_unknown(tmp_path: Path) -> None:
    assert installer.default_rc_for_shell(None, home=tmp_path) is None


def test_path_contains_finds_entry(tmp_path: Path) -> None:
    env = {"PATH": os.pathsep.join(["/usr/bin", str(tmp_path)])}
    assert installer.path_contains(tmp_path, env=env) is True


def test_path_contains_resolves_symlinks(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real_dir)
    env = {"PATH": str(link)}
    assert installer.path_contains(real_dir, env=env) is True


def test_path_contains_missing(tmp_path: Path) -> None:
    env = {"PATH": "/usr/bin:/bin"}
    assert installer.path_contains(tmp_path, env=env) is False


def test_path_update_snippet_bash_zsh(tmp_path: Path) -> None:
    assert installer.path_update_snippet("bash", tmp_path) == f'export PATH="{tmp_path}:$PATH"'
    assert installer.path_update_snippet("zsh", tmp_path) == f'export PATH="{tmp_path}:$PATH"'


def test_path_update_snippet_fish(tmp_path: Path) -> None:
    assert installer.path_update_snippet("fish", tmp_path) == f"fish_add_path -gp {tmp_path}"


def test_update_path_in_rc_creates_file(tmp_path: Path) -> None:
    rc = tmp_path / "rc"
    snippet = 'export PATH="/foo:$PATH"'
    changed = installer.update_path_in_rc(rc, snippet)
    assert changed is True
    contents = rc.read_text()
    assert installer.MARKER_BEGIN in contents
    assert installer.MARKER_END in contents
    assert snippet in contents


def test_update_path_in_rc_is_idempotent(tmp_path: Path) -> None:
    rc = tmp_path / "rc"
    snippet = 'export PATH="/foo:$PATH"'
    assert installer.update_path_in_rc(rc, snippet) is True
    assert installer.update_path_in_rc(rc, snippet) is False
    # Only one managed block
    assert rc.read_text().count(installer.MARKER_BEGIN) == 1


def test_update_path_in_rc_refreshes_snippet(tmp_path: Path) -> None:
    rc = tmp_path / "rc"
    rc.write_text(
        "# existing stuff\n"
        f"{installer.MARKER_BEGIN}\n"
        'export PATH="/old:$PATH"\n'
        f"{installer.MARKER_END}\n"
        "# trailing stuff\n"
    )
    changed = installer.update_path_in_rc(rc, 'export PATH="/new:$PATH"')
    assert changed is True
    contents = rc.read_text()
    assert "/old" not in contents
    assert "/new" in contents
    assert "# trailing stuff" in contents
    assert contents.count(installer.MARKER_BEGIN) == 1


def test_update_path_in_rc_appends_to_existing_without_marker(tmp_path: Path) -> None:
    rc = tmp_path / "rc"
    rc.write_text("# user content with no trailing newline")
    changed = installer.update_path_in_rc(rc, 'export PATH="/foo:$PATH"')
    assert changed is True
    contents = rc.read_text()
    assert contents.startswith("# user content with no trailing newline\n")
    assert installer.MARKER_BEGIN in contents


def test_remove_path_block_from_rc(tmp_path: Path) -> None:
    rc = tmp_path / "rc"
    rc.write_text(
        "# user content\n"
        f"{installer.MARKER_BEGIN}\n"
        'export PATH="/foo:$PATH"\n'
        f"{installer.MARKER_END}\n"
        "# more user content\n"
    )
    changed = installer.remove_path_block_from_rc(rc)
    assert changed is True
    contents = rc.read_text()
    assert installer.MARKER_BEGIN not in contents
    assert "# user content" in contents
    assert "# more user content" in contents


def test_remove_path_block_from_rc_no_op(tmp_path: Path) -> None:
    rc = tmp_path / "rc"
    rc.write_text("# user content only\n")
    assert installer.remove_path_block_from_rc(rc) is False


def test_remove_path_block_from_rc_missing_file(tmp_path: Path) -> None:
    assert installer.remove_path_block_from_rc(tmp_path / "missing") is False


# --- Coverage for the DRY helpers introduced by the refactor. ---------------


def test_format_managed_block_round_trip() -> None:
    """The managed-block formatter and parser regex agree on the same shape."""
    block = installer._format_managed_block('export PATH="/foo:$PATH"')
    assert block.startswith(installer.MARKER_BEGIN + "\n")
    assert block.endswith(installer.MARKER_END + "\n")
    match = installer._MANAGED_BLOCK_RE.search(block)
    assert match is not None
    assert match.group(0).rstrip("\n") == block.rstrip("\n")


def test_managed_block_regex_is_non_greedy() -> None:
    """Two managed blocks in a single file should match independently, not as one big span."""
    text = (
        f"{installer.MARKER_BEGIN}\nA\n{installer.MARKER_END}\n"
        "# user content\n"
        f"{installer.MARKER_BEGIN}\nB\n{installer.MARKER_END}\n"
    )
    matches = installer._MANAGED_BLOCK_RE.findall(text)
    assert len(matches) == 2


def test_env_helper_returns_provided_dict() -> None:
    custom = {"PATH": "/x"}
    assert installer._env(custom) is custom


def test_env_helper_falls_back_to_os_environ() -> None:
    assert installer._env(None) is os.environ


def test_same_file_true_for_identical_paths(tmp_path: Path) -> None:
    file = tmp_path / "kickstart"
    file.write_text("x")
    assert installer._same_file(file, file) is True


def test_same_file_true_through_symlink(tmp_path: Path, single_file_binary: Path) -> None:
    link = tmp_path / "alias"
    link.symlink_to(single_file_binary)
    assert installer._same_file(link, single_file_binary) is True


def test_same_file_false_for_distinct_paths(tmp_path: Path) -> None:
    a = tmp_path / "a"
    a.write_text("a")
    b = tmp_path / "b"
    b.write_text("b")
    assert installer._same_file(a, b) is False


def test_safe_resolve_falls_back_to_absolute(tmp_path: Path) -> None:
    path = tmp_path / "x"
    assert installer._safe_resolve(path) == path.resolve()


def test_default_rc_uses_layout_table(tmp_path: Path) -> None:
    """default_rc_for_shell should pull from the single declarative layout table."""
    assert "zsh" in installer._SHELL_RC_LAYOUT
    assert "bash" in installer._SHELL_RC_LAYOUT
    assert "bash-darwin" in installer._SHELL_RC_LAYOUT
    assert "fish" in installer._SHELL_RC_LAYOUT
    result = installer.default_rc_for_shell("zsh", home=tmp_path)
    assert result is not None
    assert result.parts[-1:] == installer._SHELL_RC_LAYOUT["zsh"]


def test_install_then_uninstall_round_trip(tmp_path: Path, single_file_binary: Path) -> None:
    """A full install + uninstall cycle leaves the install dir empty and is idempotent on uninstall."""
    target_dir = tmp_path / "user-bin"
    installer.install_binary(single_file_binary, target_dir)
    assert (target_dir / installer.BINARY_NAME).exists()
    removed = installer.uninstall_binary(target_dir)
    assert removed == target_dir / installer.BINARY_NAME
    assert installer.uninstall_binary(target_dir) is None


def test_update_path_in_rc_only_refreshes_first_block(tmp_path: Path) -> None:
    """If a file ended up with two managed blocks, we only touch the first."""
    rc = tmp_path / "rc"
    rc.write_text(
        f"{installer.MARKER_BEGIN}\nA\n{installer.MARKER_END}\n"
        "# middle\n"
        f"{installer.MARKER_BEGIN}\nB\n{installer.MARKER_END}\n"
    )
    installer.update_path_in_rc(rc, 'export PATH="/new:$PATH"')
    contents = rc.read_text()
    assert contents.count(installer.MARKER_BEGIN) == 2
    assert "/new" in contents
    assert "B" in contents


def test_update_path_in_rc_handles_empty_file(tmp_path: Path) -> None:
    rc = tmp_path / "rc"
    rc.write_text("")
    changed = installer.update_path_in_rc(rc, 'export PATH="/foo:$PATH"')
    assert changed is True
    assert rc.read_text().startswith(installer.MARKER_BEGIN)


def test_path_contains_handles_missing_path_var(tmp_path: Path) -> None:
    assert installer.path_contains(tmp_path, env={}) is False


def test_install_binary_falls_back_on_resolve_failure(tmp_path: Path, single_file_binary: Path, monkeypatch) -> None:
    """`_same_file` should swallow OSError and still let the install proceed."""
    target_dir = tmp_path / "user-bin"
    target_dir.mkdir()
    destination = target_dir / installer.BINARY_NAME
    destination.write_text("old")

    original_resolve = Path.resolve

    def flaky_resolve(self: Path, *, strict: bool = False) -> Path:
        if self == destination:
            raise OSError("boom")
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", flaky_resolve)
    result = installer.install_binary(single_file_binary, target_dir, overwrite=True)
    assert result.copied is True
    assert destination.read_text() == single_file_binary.read_text()


def test_install_binary_expands_relative_target(tmp_path: Path, single_file_binary: Path) -> None:
    """install_binary should accept a relative path and create the directory."""
    relative_target = tmp_path / "nested" / "bin"
    result = installer.install_binary(single_file_binary, relative_target)
    assert relative_target.exists()
    assert result.destination == relative_target / installer.BINARY_NAME
    assert result.destination.exists()


# --- Onedir bundle install path -----------------------------------------


def _make_fake_onedir_bundle(root: Path, *, bundle_name: str = "kickstart-bundle") -> Path:
    """Build a directory that looks like a PyInstaller --onedir output.

    Returns the path to the launcher inside the bundle; the bundle directory is
    the launcher's parent.
    """
    bundle = root / bundle_name
    (bundle / "_internal").mkdir(parents=True)
    (bundle / "_internal" / "marker").write_text("present\n")
    launcher = bundle / installer.BINARY_NAME
    launcher.write_text("#!/bin/sh\necho fresh\n")
    launcher.chmod(0o755)
    return launcher


def test_onedir_bundle_root_detects_pyinstaller_layout(tmp_path: Path) -> None:
    launcher = _make_fake_onedir_bundle(tmp_path)
    bundle_root = installer._onedir_bundle_root(launcher)
    assert bundle_root == launcher.parent


def test_onedir_bundle_root_ignores_single_file(tmp_path: Path, single_file_binary: Path) -> None:
    """A bare single-file binary is NOT a bundle root."""
    assert installer._onedir_bundle_root(single_file_binary) is None


def test_onedir_bundle_root_ignores_non_kickstart_filename(tmp_path: Path) -> None:
    """The detector keys off the BINARY_NAME — other names don't qualify."""
    bundle = tmp_path / "bundle"
    (bundle / "_internal").mkdir(parents=True)
    other = bundle / "not-kickstart"
    other.write_text("#!/bin/sh\n")
    other.chmod(0o755)
    assert installer._onedir_bundle_root(other) is None


def test_install_binary_installs_onedir_bundle_via_symlink(tmp_path: Path) -> None:
    """install_binary copies the bundle directory under app_root and symlinks the launcher."""
    launcher = _make_fake_onedir_bundle(tmp_path / "src")
    target_dir = tmp_path / "user" / "bin"
    app_root = tmp_path / "user" / "share" / "kickstart"

    result = installer.install_binary(launcher, target_dir, app_root=app_root)

    bundle_dest = app_root / installer.APP_DIR_NAME
    launcher_dest = target_dir / installer.BINARY_NAME

    assert bundle_dest.is_dir()
    assert (bundle_dest / installer.BINARY_NAME).exists()
    assert (bundle_dest / "_internal" / "marker").read_text() == "present\n"
    assert launcher_dest.is_symlink()
    assert launcher_dest.resolve() == bundle_dest / installer.BINARY_NAME
    assert result.copied is True
    assert result.app_root == app_root
    assert result.app_path == bundle_dest


def test_install_binary_onedir_default_app_root(tmp_path: Path) -> None:
    """When app_root is omitted and target ends in /bin, default to <parent>/share/kickstart."""
    launcher = _make_fake_onedir_bundle(tmp_path / "src")
    target_dir = tmp_path / "prefix" / "bin"

    result = installer.install_binary(launcher, target_dir)
    expected_app_root = tmp_path / "prefix" / "share" / installer.BINARY_NAME
    assert result.app_root == expected_app_root
    assert (expected_app_root / installer.APP_DIR_NAME).is_dir()


def test_install_binary_onedir_alternate_default(tmp_path: Path) -> None:
    """When target does NOT end in /bin, default app_root is <target>/.kickstart."""
    launcher = _make_fake_onedir_bundle(tmp_path / "src")
    target_dir = tmp_path / "custom-launchers"

    result = installer.install_binary(launcher, target_dir)
    expected_app_root = target_dir / f".{installer.BINARY_NAME}"
    assert result.app_root == expected_app_root


def test_install_binary_onedir_refuses_overwrite_without_force(tmp_path: Path) -> None:
    """A second install of a *different* bundle must require overwrite=True."""
    first_launcher = _make_fake_onedir_bundle(tmp_path / "src-a", bundle_name="bundle-a")
    target_dir = tmp_path / "bin"
    app_root = tmp_path / "share" / "kickstart"
    installer.install_binary(first_launcher, target_dir, app_root=app_root)

    # Build a NEW bundle directory with different content so _same_file returns False.
    second_launcher = _make_fake_onedir_bundle(tmp_path / "src-b", bundle_name="bundle-b")
    (second_launcher.parent / "_internal" / "marker").write_text("v2\n")
    with pytest.raises(FileExistsError):
        installer.install_binary(second_launcher, target_dir, app_root=app_root, overwrite=False)


def test_install_binary_onedir_overwrite_replaces_bundle(tmp_path: Path) -> None:
    """overwrite=True replaces an existing bundle and re-points the launcher symlink."""
    first_launcher = _make_fake_onedir_bundle(tmp_path / "src-a", bundle_name="bundle-a")
    target_dir = tmp_path / "bin"
    app_root = tmp_path / "share" / "kickstart"
    installer.install_binary(first_launcher, target_dir, app_root=app_root)

    second_launcher = _make_fake_onedir_bundle(tmp_path / "src-b", bundle_name="bundle-b")
    (second_launcher.parent / "_internal" / "marker").write_text("v2\n")

    result = installer.install_binary(second_launcher, target_dir, app_root=app_root, overwrite=True)
    bundle_dest = app_root / installer.APP_DIR_NAME
    assert (bundle_dest / "_internal" / "marker").read_text() == "v2\n"
    assert (target_dir / installer.BINARY_NAME).resolve() == bundle_dest / installer.BINARY_NAME
    assert result.copied is True


def test_install_binary_onedir_staging_failure_preserves_active_nested_bundle(tmp_path: Path, monkeypatch) -> None:
    """A failed repair must leave the existing nested payload executable."""
    target_dir = tmp_path / "bin"
    target_dir.mkdir()
    app_root = tmp_path / "share" / "kickstart"
    bundle_dest = app_root / installer.APP_DIR_NAME
    nested_bundle = bundle_dest / ".kickstart" / installer.APP_DIR_NAME
    (nested_bundle / "_internal").mkdir(parents=True)
    nested_executable = nested_bundle / installer.BINARY_NAME
    nested_executable.write_text("#!/bin/sh\necho old\n")
    nested_executable.chmod(0o755)

    managed_executable = bundle_dest / installer.BINARY_NAME
    managed_executable.symlink_to(nested_executable)
    launcher = target_dir / installer.BINARY_NAME
    launcher.symlink_to(managed_executable)
    fresh_launcher = _make_fake_onedir_bundle(tmp_path / "fresh")

    def fail_copytree(*args, **kwargs):
        raise OSError("staging failed")

    monkeypatch.setattr(installer.shutil, "copytree", fail_copytree)

    with pytest.raises(OSError, match="staging failed"):
        installer.install_binary(fresh_launcher, target_dir, app_root=app_root, overwrite=True)

    assert launcher.resolve() == nested_executable
    assert nested_executable.read_text() == "#!/bin/sh\necho old\n"


def test_install_binary_onedir_activation_failure_restores_active_bundle(tmp_path: Path, monkeypatch) -> None:
    """A failed activation rolls the old payload back into its stable path."""
    old_launcher = _make_fake_onedir_bundle(tmp_path / "old")
    target_dir = tmp_path / "bin"
    app_root = tmp_path / "share" / "kickstart"
    installer.install_binary(old_launcher, target_dir, app_root=app_root)
    active_launcher = target_dir / installer.BINARY_NAME
    old_target = active_launcher.resolve()
    fresh_launcher = _make_fake_onedir_bundle(tmp_path / "fresh")
    (fresh_launcher.parent / "_internal" / "marker").write_text("fresh\n")

    original_rename = Path.rename

    def fail_activation(self: Path, target: Path) -> Path:
        if self.name.startswith(f".{installer.APP_DIR_NAME}.tmp-"):
            raise OSError("activation failed")
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", fail_activation)

    with pytest.raises(OSError, match="activation failed"):
        installer.install_binary(fresh_launcher, target_dir, app_root=app_root, overwrite=True)

    assert active_launcher.resolve() == old_target
    assert (app_root / installer.APP_DIR_NAME / "_internal" / "marker").read_text() == "present\n"


def test_install_binary_onedir_idempotent_same_bundle(tmp_path: Path) -> None:
    """Re-installing the same bundle is a no-op for both the payload and launcher."""
    launcher = _make_fake_onedir_bundle(tmp_path / "src")
    target_dir = tmp_path / "bin"
    app_root = tmp_path / "share" / "kickstart"
    installer.install_binary(launcher, target_dir, app_root=app_root)

    # Now re-install pointing at the freshly-installed bundle (the source IS the
    # destination after the first install).
    new_source = app_root / installer.APP_DIR_NAME / installer.BINARY_NAME
    second_result = installer.install_binary(new_source, target_dir, app_root=app_root, overwrite=True)
    assert second_result.copied is False
    assert second_result.already_installed is True


def test_uninstall_binary_removes_onedir_payload(tmp_path: Path) -> None:
    """uninstall_binary removes both the launcher and the entire app_root directory."""
    launcher = _make_fake_onedir_bundle(tmp_path / "src")
    target_dir = tmp_path / "bin"
    app_root = tmp_path / "share" / "kickstart"
    installer.install_binary(launcher, target_dir, app_root=app_root)

    removed = installer.uninstall_binary(target_dir, app_root=app_root)
    assert removed == target_dir / installer.BINARY_NAME
    assert not (target_dir / installer.BINARY_NAME).exists()
    assert not app_root.exists()


def test_install_launcher_falls_back_to_wrapper_script(tmp_path: Path, monkeypatch) -> None:
    """When symlink_to raises, _install_launcher writes an exec wrapper instead."""
    launcher = _make_fake_onedir_bundle(tmp_path / "src")
    target_dir = tmp_path / "bin"
    app_root = tmp_path / "share" / "kickstart"

    original_symlink_to = Path.symlink_to

    def refusing_symlink(self: Path, target, *args, **kwargs):
        # Force the failure once for the user-bin launcher; let everything else
        # through (e.g. extracted-archive internal symlinks).
        if self == target_dir / installer.BINARY_NAME:
            raise OSError("simulated: filesystem refuses symlinks")
        return original_symlink_to(self, target, *args, **kwargs)

    monkeypatch.setattr(Path, "symlink_to", refusing_symlink)
    installer.install_binary(launcher, target_dir, app_root=app_root)

    wrapper = target_dir / installer.BINARY_NAME
    assert wrapper.exists()
    assert not wrapper.is_symlink()
    body = wrapper.read_text()
    assert body.startswith("#!/bin/sh")
    assert str(app_root / installer.APP_DIR_NAME / installer.BINARY_NAME) in body
