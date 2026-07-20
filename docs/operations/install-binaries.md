# Install Binaries

Release tags publish a prebuilt kickstart binary as a `.tar.gz` archive for:

- `linux-x64`
- `linux-arm64`
- `macos-arm64`

Each platform is built for Python `3.14`. Platforms outside this matrix
(for example Intel macOS) install from source
(`pipx install git+https://github.com/woud420/kickstart`) or from the
wheel attached to each GitHub Release. Do not `pip install kickstart`:
the PyPI name belongs to an unrelated, abandoned 2011 project.

Release wheels and binary archives contain the public PostHog capture
configuration. Telemetry is enabled by default for eligible commands, but an
explicit `kickstart telemetry disable`, `DO_NOT_TRACK=1`, or
`KICKSTART_TELEMETRY_DISABLED=1` always wins. Direct Git source installs do not
contain the capture configuration; delivery from one requires
`POSTHOG_PUBLIC_CUSTOMER_API_TOKEN` in the process environment as well as an
otherwise eligible event.

The `cli_install_completed` event refers only to an invocation of the
`kickstart install` command, including the PATH-configuration invocation made
by the shell installer when applicable. The shell download/copy itself, `pip`,
`pipx`, package managers, and manual file copies are not independently counted.
Likewise, `cli_upgrade_completed` refers only to `kickstart upgrade`, so these
events are not universal installation or upgrade totals.

To prevent even the first `kickstart install` event, set either process-level
opt-out on that invocation:

```bash
KICKSTART_TELEMETRY_DISABLED=1 ./kickstart-macos-arm64-py3.14/kickstart install --update-path
# Or, when DO_NOT_TRACK is your standard environment-wide preference:
DO_NOT_TRACK=1 ./kickstart-macos-arm64-py3.14/kickstart install --update-path

# Suppress an installer-invoked event from the quick-install process:
curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh \
  | KICKSTART_TELEMETRY_DISABLED=1 bash
```

Those environment settings apply to the current process. Run
`kickstart telemetry disable` to persist the preference for later commands.

## Asset Names

```text
kickstart-linux-x64-py3.14.tar.gz
kickstart-linux-arm64-py3.14.tar.gz
kickstart-macos-arm64-py3.14.tar.gz
```

Releases before `v0.4.1` also shipped `macos-x64` and Python `3.12`/`3.13`
variants using the same naming pattern. Each archive has a matching
`<asset>.tar.gz.sha256` file for integrity checks.

## Quick Install

The repo ships an installer script that picks the right asset, verifies the
checksum, lays out the launcher, and offers to update your shell `PATH`:

```bash
curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh | bash
```

Recognised environment variables:

| Env var | Matching flag | Default | Purpose |
| --- | --- | --- | --- |
| `KICKSTART_VERSION` | `--version` | latest | Release tag to install |
| `KICKSTART_INSTALL_DIR` | `--target` | `~/.local/bin` | Launcher directory |
| `KICKSTART_APP_ROOT` | `--app-dir` | derived from `--target` | Binary payload directory |
| `KICKSTART_PYTHON_MINOR` | `--python-minor` | `3.14` | Python minor of the archive |
| `KICKSTART_UPDATE_PROFILE` | `--no-path-update` / `--yes` | `prompt` | `prompt`, `yes`, or `no` (skip PATH update) |
| `KICKSTART_ASSUME_YES` | `--yes` | `0` | Set to `1` to accept the PATH prompt non-interactively |
| `KICKSTART_REPO` | (none) | `woud420/kickstart` | `owner/repo` to install from |

Pass `--help` for the same information from the script. `scripts/install.sh`
is attached to every GitHub Release if you want to pin to a tagged copy of
the installer.

## Manual Install

Substitute your platform, Python minor, and version when downloading a
different asset. The `.tar.gz` binary archive format is the supported install
path; pre-`v0.4.0` releases and `v0.4.0` itself ship the older single-file
asset layout and cannot be installed with the flow below — pick a newer tag
from the [Releases page](https://github.com/woud420/kickstart/releases).

```bash
PLATFORM=macos-arm64
PY=3.14
TAG=v<TAG>   # browse https://github.com/woud420/kickstart/releases for tags

curl -L -o "kickstart-${PLATFORM}-py${PY}.tar.gz" \
  "https://github.com/woud420/kickstart/releases/download/${TAG}/kickstart-${PLATFORM}-py${PY}.tar.gz"

# Optional: verify integrity.
curl -L -o "kickstart-${PLATFORM}-py${PY}.tar.gz.sha256" \
  "https://github.com/woud420/kickstart/releases/download/${TAG}/kickstart-${PLATFORM}-py${PY}.tar.gz.sha256"
shasum -a 256 -c "kickstart-${PLATFORM}-py${PY}.tar.gz.sha256"

tar -xzf "kickstart-${PLATFORM}-py${PY}.tar.gz"
```

The archive contains a single top-level directory (named like the asset
without the `.tar.gz` suffix) holding the kickstart launcher and its onedir
payload. Use kickstart's own installer to copy the payload into a stable
directory and expose the launcher on `PATH`:

```bash
./kickstart-macos-arm64-py3.14/kickstart install --update-path
# Drops a symlink at ~/.local/bin/kickstart pointing into
# ~/.local/share/kickstart/current/kickstart and edits the appropriate
# shell rc file (~/.zshrc, ~/.bash_profile, or ~/.config/fish/config.fish).

# Custom locations:
./kickstart-macos-arm64-py3.14/kickstart install \
  --target /usr/local/bin \
  --app-dir /usr/local/share/kickstart

# Inspect status without modifying anything:
./kickstart-macos-arm64-py3.14/kickstart install --check

# Force an overwrite if the destination already holds a kickstart binary:
./kickstart-macos-arm64-py3.14/kickstart install --force

# Override `$SHELL` detection (use when CI / non-login shells set it oddly):
./kickstart-macos-arm64-py3.14/kickstart install --shell bash   # or zsh, fish

# Remove the launcher and binary payload, optionally restoring the rc file:
./kickstart-macos-arm64-py3.14/kickstart uninstall --clean-path
```

If your filesystem doesn't allow symlinks (rare), `kickstart install` falls
back to writing a tiny `#!/bin/sh` wrapper at the target path. The wrapper
behaves identically for users.

## Local Development Entrypoint

This section is the maintainer-facing contract for what the `kickstart` command
on `PATH` should resolve to, so a stale entrypoint can always be diagnosed and
repaired.

The canonical install is the one this document describes: a launcher at
`~/.local/bin/kickstart` (symlink or `#!/bin/sh` wrapper), owned by
`kickstart install`, which leads to the active managed payload under
`~/.local/share/kickstart`. `kickstart upgrade` refreshes that managed
installation while reusing the same launcher and managed app root on every
run. A successful upgrade also collapses an accidentally nested payload left
by older upgrade logic back into that stable root. Treat the payload's
internal path as an implementation detail and use `kickstart install --check`
to inspect it. Nothing else should shadow the launcher. In particular, ad-hoc
shims in personal `bin` directories (for example
`~/workspace/bin/kickstart`) are not supported: they bypass `kickstart
upgrade`, go stale silently, and hide which binary owns the command. Delete
them, or reduce them to a one-line `exec "$HOME/.local/bin/kickstart" "$@"`
that cannot drift.

To track the repo instead of a release (maintainer workflow), install the
working copy as a tool so the entrypoint follows local changes:

```bash
uv tool install --editable /path/to/kickstart   # or: pipx install --editable
```

Diagnose the current entrypoint state at any time:

```bash
which -a kickstart        # every match on PATH, in resolution order
kickstart install --check # source, destination, payload dir, PATH status
```

`which -a` showing more than one path, or `install --check` reporting a missing
destination, means a shadowing shim or a stale install — repair with the steps
above.

## Self-Update

Once installed, refresh in place against the newest release:

```bash
kickstart upgrade
```

`kickstart upgrade` discovers the asset matching the running host's platform
and Python minor, verifies its SHA-256 against the published `.sha256` file,
and re-uses the same installer code path described above to refresh the active
managed installation. Do not script against the payload's internal directory;
use `kickstart install --check` to inspect it.
