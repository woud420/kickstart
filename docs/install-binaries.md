# Install Binaries

Release tags build downloadable standalone binaries for:

- `linux-x64`
- `linux-arm64`
- `macos-x64`
- `macos-arm64`

Each platform is built for Python `3.12`, `3.13`, and `3.14`.

## Asset Names

```text
kickstart-linux-x64-py3.14
kickstart-linux-arm64-py3.14
kickstart-macos-x64-py3.14
kickstart-macos-arm64-py3.14
```

Older supported Python minors use the same pattern, for example `kickstart-macos-arm64-py3.12`.

## Install

Replace the version and platform suffix when installing a different release or architecture. The project supports releases from `v0.4.0` onward.

```bash
curl -L -o kickstart "https://github.com/woud420/kickstart/releases/download/v0.4.0/kickstart-macos-arm64-py3.14"
chmod +x kickstart
./kickstart version
```

Move it onto your `PATH` when you want it available globally:

```bash
mkdir -p ~/.local/bin
install -m 0755 kickstart ~/.local/bin/kickstart
```

Each binary has a matching `.sha256` file for integrity checks.
