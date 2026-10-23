# Homebrew distribution

The custom tap is [woud420/homebrew-tap](https://github.com/woud420/homebrew-tap).
Install it directly, or add the tap first:

```bash
brew install woud420/tap/kickstart
# Equivalent explicit tap setup:
brew tap woud420/tap
brew install woud420/tap/kickstart

brew update
brew upgrade woud420/tap/kickstart
brew uninstall woud420/tap/kickstart
```

The formula consumes the project's stable GitHub binary archives, pinned by tag
and SHA-256. It bundles Python and the CLI dependencies; it does not use PyPI.
The initial supported targets are Apple Silicon on macOS 15 or newer and
x86_64/arm64 Linux with glibc 2.39 or newer (tested on Ubuntu 24.04). Intel macOS,
musl Linux, Windows, and other CPUs use the source/wheel installation instructions
in [Install binaries](install-binaries.md). Homebrew rejects Intel macOS through
the formula's architecture requirement. Earlier Linux glibc versions cannot run
the release binaries; use the source installation there.

## Package ownership and migration

Homebrew installs the payload into its versioned Cellar and links a launcher onto
PATH. That launcher refuses `kickstart install`, `upgrade`, `uninstall`, and the
internal upgrade handoff, including `kickstart -- upgrade`. Use the `brew`
commands above for the package lifecycle. Invoke the public `kickstart` launcher;
the executable inside `libexec` is an internal payload and has no supported
standalone lifecycle.

An earlier `~/.local/bin/kickstart` may appear first on PATH. Before switching,
use that standalone installation's `kickstart uninstall --clean-path`, then
install through Homebrew and check `command -v kickstart` and `kickstart version`.
Do not point the standalone shell installer at Homebrew's prefix or Cellar.
Homebrew uninstall preserves the user's telemetry preference and generated repos.
Release builds enable pseudonymous telemetry by default; `kickstart telemetry
disable`, `KICKSTART_TELEMETRY_DISABLED=1`, and `DO_NOT_TRACK=1` retain their usual
meaning. Formula smoke tests disable telemetry.

## Release updates

The release workflow calls `Homebrew Distribution` after GitHub publishes the
release assets. It downloads the three platform archives and their checksum
sidecars, fails on any mismatch or missing file, then renders `ci/homebrew.py`.
Three native jobs check formula style/audit, install v0.4.5, upgrade to the candidate,
generate a Python library, verify the ownership guards, and uninstall. Only a
successful matrix permits the formula update on the tap's `main` branch.

Configure the `HOMEBREW_TAP_TOKEN` Actions secret in **woud420/kickstart** with a
dedicated fine-grained token: repository access only to **woud420/homebrew-tap**,
Contents read/write, and the required Metadata read permission. It needs no
workflows or organization permissions. Keep its expiration/rotation in the
maintainer's credential records. The normal `GITHUB_TOKEN` reads release assets;
the tap token is only available to the final publication job. Pull requests run
the smoke matrix against v0.4.6 without publication credentials.

The tap also checks its formula on macOS arm64 and Linux x64/arm64 for pushes and
pull requests. No recurring polling job is required.

### Recovery or initial publication

After configuring or rotating the secret, rerun the failed publication job, or
dispatch the workflow for the already-published tag:

```bash
gh workflow run homebrew.yml --repo woud420/kickstart -f tag=v0.4.6
```

For a manual update, download and verify the release, generate the formula, then
review and push it to the tap using your normal Git credentials:

```bash
gh release download v0.4.6 --repo woud420/kickstart \
  --pattern 'kickstart-*-py3.14.tar.gz*' --dir artifacts/homebrew
python3 ci/homebrew.py --tag v0.4.6 --artifacts artifacts/homebrew \
  --output ../homebrew-tap/Formula/kickstart.rb
```

Run the tap's CI before publishing a manual formula change. The lifecycle smoke
script requires a disposable Homebrew environment without an existing kickstart
installation or tap. A failed tap job does not undo an already-published GitHub
Release or website deployment. Same-version retags regenerate checksums after
artifact replacement; never retain a stale formula checksum for rebuilt assets.
