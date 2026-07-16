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

## Self-Update

Once installed, refresh in place against the newest release:

```bash
kickstart upgrade
```

`kickstart upgrade` discovers the asset matching the running host's platform
and Python minor, verifies its SHA-256 against the published `.sha256` file,
and re-uses the same installer code path described above to replace the
launcher and refresh the binary payload directory.
