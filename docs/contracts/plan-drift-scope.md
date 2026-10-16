# Plan Command Drift Scope

Checked: 2026-07-15

`kickstart plan REPO [--json]` is the read-only docs-drift frontend. This
contract pins what it covers, what it deliberately defers, and its output
shape, so the broader drift work builds on it instead of forking it.

## Covered

Exactly the registry-rendered markdown projections
(`src/generator/projections.py`) inside their ownership fences: `AGENTS.md`
and the `docs/{contracts,operations,decisions}` READMEs, re-rendered from
`.kickstart/scaffold.json` via `ScaffoldContract.from_manifest` and compared
byte-for-byte against the fenced region on disk. The architecture README is
presence-checked only: its content needs generation-time inputs (title,
directory list) a schema-3.0 manifest does not record.

Statuses: `in-sync`, `presence-only` (both clean); `would-create`,
`content-drift` (unified diff attached), `unfenced` (pre-fence scaffold or
hand-written file — a structural fact, content never compared),
`malformed-markers`, `unreadable` (all findings).

Schema 3.2 Worker manifests record `project.language`: TypeScript selects only
the TypeScript Worker docs profile, and Rust selects only the default profile.
Legacy manifests without language still match either profile. An unsupported
explicit Worker language is a target error, rather than an ambiguous fallback.

## Deferred — and to whom

- Full managed-envelope drift (Makefile targets, CI workflows, artifact
  files) and drift classes for co-owned files: the drift check built on
  schema 4.0 (ENG-12 on ENG-159). `plan` is its docs-projection library
  sibling (`src/generator/docs_plan.py`, alongside `adoption.py`), not a fork.
- Inserting fences or the manifest into pre-fence repos: the adopt write path
  (ENG-11). `plan` never writes.
- Recovering architecture render inputs from the manifest: the manifest still
  lacks the title and directory list. Worker profile selection is recovered
  from explicit language; legacy manifests without it remain ambiguous.

## Exit codes and JSON

Exit 0 = every entry clean; 1 = at least one finding; 2 = usage error (no
repository, or no plannable manifest). `--json` emits
`{"root", "in_sync", "entries": [{"artifact", "target", "status", "detail",
"diff", "profile"}]}` — the `adopt --check` report pattern.
