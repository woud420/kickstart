# Changelog

Notable changes per release. The website release section
(`website/src/site/content.ts`) carries the same entries and is
test-enforced to include the current `pyproject.toml` version, so the
public changelog cannot silently fall behind a release.

Release mechanics live in [docs/release-policy.md](docs/release-policy.md).

## v0.4.2 - 2026-06-12

### Fixed

- `kickstart version` reports the installed release again. The 0.4.1
  binaries printed `v0.4.0` because the release bumped `pyproject.toml`
  but not the runtime `src/__init__.py:__version__` that the CLI reads.
- The release website deploy job no longer fails on Alchemy's CI
  local-state-store guard. The Worker and its custom domain deploy with
  `adopt: true`, so ephemeral CI state converges on the same named
  resources; optional `ALCHEMY_PASSWORD` / `ALCHEMY_STATE_TOKEN` secrets
  upgrade deploys to a persistent Cloudflare state store.

### Added

- `make release-check` (and the release workflow) now fails when
  `pyproject.toml` and `src/__init__.py` disagree, closing the version
  desync class of bug for good.
- Website changelog: the release section now lists every release with
  curated highlights, kept current by tests.

## v0.4.1 - 2026-06-04

### Changed

- Every generated Makefile exposes the same canonical verbs
  (`install, dev, test, lint, fmt, format-check, typecheck, check, build`,
  plus `docker-build` where applicable) across Python, Rust, Go,
  TypeScript, and C++.
- Generated Python CI consumes the pinned Poetry version from the
  toolchain source of truth instead of an unpinned install.
- Release binary matrix focused to py3.14 on linux-x64, linux-arm64, and
  macos-arm64; other platforms install from PyPI.

### Fixed

- Python service containers install runtime dependencies, expose their
  port, and bind to `0.0.0.0` so the generated image actually serves.

## v0.4.0 - 2026-05-06

First supported baseline.

### Added

- Typed specs, layout plans, stack registry, template plans, and
  agent-readable scaffold docs (`.kickstart/scaffold.json`, `AGENTS.md`,
  `docs/contracts`, `docs/operations`, `docs/decisions`).
- Service extension capabilities: Postgres, Redis, and JWT across
  supported languages, validated as an explicit capability matrix.
- Cloudflare provider and Worker scaffolding, including TypeScript and
  Rust Workers, with the website itself served by a kickstart Worker.
- Linux/macOS binary release workflow with SHA-256 checksums and a
  one-line install script.

Older history lives in the
[GitHub releases](https://github.com/woud420/kickstart/releases).
