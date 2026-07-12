# Changelog

Notable changes per release. The website release section
(`website/src/site/content.ts`) carries the same entries and is
test-enforced to include the current `pyproject.toml` version — in
`bun run check`, per-PR CI, and the release workflow's verify job — so
the website source cannot fall behind a version bump. Deployed-site
parity is a release-time property: the site updates when the release
tag's Deploy Website job runs, and the weekly release-drift check fails
if a merged version ever sits untagged.

Release mechanics live in [docs/release-policy.md](docs/release-policy.md).

## v0.4.3 - 2026-06-26

Repo-quality release: no change to generated project behavior or installed CLI,
but the development and release machinery around kickstart got materially better.

### Added

- SessionStart hook (`.claude/hooks/session-start.sh`) bootstraps the Claude
  Code on the web sandbox: pins Poetry to a supported interpreter, installs
  Python and website dependencies, so `make check` and the website checks work
  immediately in a fresh remote session.
- Tiered eval runner: `scripts/run_evals.py --tier smoke|pr|full` runs the eval
  suite from one entrypoint with a single summary table and a non-zero exit on
  any failing step.
- Scaffold-weight regression baselines: `token_savings_eval.py --check-baselines`
  fails when generated output changes file count or drifts beyond ±10% of the
  committed `tests/fixtures/scaffold-weight-baselines.json`; `--update-baselines`
  acknowledges deliberate changes. The regression guard for the token-efficiency
  promise, modeled on practices studied from the headroom benchmark suite
  (`docs/decisions/headroom-benchmark-learnings.md`).
- Test coverage: `make coverage` measures `src/` + `ci/` (88.1% baseline); a CI
  job uploads to Codecov (fail-soft without the token). The README leads with
  CI, Release, Scheduled Evals, Codecov, and latest-release badges.

### Changed

- Docs and the `kickstart` skill standardized scratch paths on `/tmp` (the
  macOS-specific `/private/tmp` is not canonical on Linux sandboxes).

## v0.4.2 - 2026-06-12

### Fixed

- `kickstart version` reports the installed release again. The 0.4.1
  binaries printed `v0.4.0` because the release bumped `pyproject.toml`
  but not the runtime `src/__init__.py:__version__` that the CLI reads.
- CLI exit codes are trustworthy: unsupported project types, failed or
  skipped creation (existing directory), and misapplied options
  (`--helm` on a CLI) now exit non-zero with specific errors instead of
  printing a warning and exiting 0.
- Project names are validated (lowercase, starts with a letter; letters,
  digits, dashes, underscores). Path traversal via names like `../evil`
  previously wrote outside `--root` with a success banner.
- `kickstart adopt --check --json` emits raw JSON; it previously routed
  through rich, which hard-wrapped long paths (invalid JSON) and ate
  bracketed path segments.
- Generated Python JWT services pass their own `make check` again
  (modern `type` aliases instead of `TypeAlias`, import-block spacing),
  and password hashing uses maintained `bcrypt` directly — the new
  generated tests caught `passlib` breaking against `bcrypt>=4.1`.
- Generated Rust toolchain pin bumped to 1.88 (extension dependency
  trees now require it; caught by generating and checking for real).
- Generated Python Makefiles no longer leak the project into an active
  virtualenv: `POETRY_IGNORE_ACTIVE_VIRTUALENVS` is not a real Poetry
  setting, so running `make install` inside any activated venv installed
  the generated project there. The Makefiles now unset `VIRTUAL_ENV` so
  Poetry always uses the in-project `.venv`.
- A 20-run cold-start agent evaluation surfaced and fixed four more
  generated-project bugs: the minimal-framework Python service failed
  strict mypy and disagreed with its own smoke test; Rust services with
  extensions stopped compiling when `time >= 0.3.48` met actix-web's
  `cookie 0.16` (the generated Cargo.toml now pins `time < 0.3.48` with
  a removal note); the C++ Makefile's `**` globs silently matched
  nothing under `/bin/sh` and hid unformatted sources (now `find`-based,
  sources clang-format-clean); Helm charts hardcoded `example-service`
  instead of the project name (now parameterized).
- First-contact ergonomics from the same evaluation: `--version` flag,
  `--root` defaults to the working directory instead of prompting,
  enumerated project types/languages and an examples epilog in
  `create --help`, and a post-create next-steps line naming `make check`.
- `kickstart adopt --check` now verifies the Makefile exposes a `check`
  target instead of only checking existence, and documents its exit
  codes (0 complete / 1 gaps / 2 usage error).
- The interactive wizard exits with a specific message on EOF instead of
  dumping a traceback and exiting 0.
- The release website deploy job no longer fails on Alchemy's CI
  local-state-store guard. The Worker and its custom domain deploy with
  `adopt: true`, so ephemeral CI state converges on the same named
  resources; optional `ALCHEMY_PASSWORD` / `ALCHEMY_STATE_TOKEN` secrets
  upgrade deploys to a persistent Cloudflare state store.

### Added

- `kickstart adopt --check`: read-only inspection of an existing repo
  against the scaffold standard, with `--json` output for agents and CI.
  Writing/applying remains a future, explicit step.
- `make release-check` (and the release workflow) now fails when
  `pyproject.toml` and `src/__init__.py` disagree, closing the version
  desync class of bug for good.
- Website changelog: the release section now lists every release with
  curated highlights, kept current by tests; showcased command examples
  are regenerated and verified against real output in CI.
- Evals: bootstrap gate (kickstart must bootstrap a kickstart-like project
  that passes taste rules and its own `make check` — four cases gate every
  PR, the full matrix runs weekly against live toolchains), token-savings
  measurement, and byte-identical determinism tests.
- Generated projects ship real tests instead of `assert True`: services
  verify their own health route, and every selected extension carries
  infrastructure-free tests (JWT roundtrip/tamper/password, Redis and
  Postgres client behavior — Python, Rust, and TypeScript). A
  `capability-tests` eval rule fails any scaffold whose manifest declares
  a capability no test exercises.
- Generated `docs/architecture/README.md` is a real module map (each
  directory with its purpose, selected capabilities, where to start
  reading) instead of a bare heading — written for humans navigating
  agent-written repos.
- Auto-tagging: merging a version bump to `master` creates the release tag
  automatically (gated on `make release-check`, idempotent, requires the
  `RELEASE_TAG_TOKEN` secret so the tag push can trigger the release).

### Changed

- `.kickstart/scaffold.json` schema 3.0: the static `option_semantics`
  glossary is replaced by a `semantics` URL pointing at
  `docs/scaffold-contract.md`, shrinking every generated manifest by more
  than half (~295 tokens saved per agent read, per repo).

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
