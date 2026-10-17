# Plan Command Drift Scope

Checked: 2026-07-15

`kickstart plan REPO [--json]` is the read-only docs-drift frontend. This
contract pins what it covers, what it deliberately defers, and its output
shape, so the broader drift work builds on it instead of forking it.

## Covered

The content-comparison scope follows the registry-rendered markdown projections
(`src/generator/projections.py`, with identities in `managed_artifacts.py`):

- `AGENTS.md`
- `CLAUDE.md`
- `.agents/skills/README.md`
- `docs/contracts/README.md`
- `docs/operations/README.md`
- `docs/decisions/README.md`

Each is re-rendered from `.kickstart/scaffold.json` via
`ScaffoldContract.from_manifest` and compared byte-for-byte only inside its named
ownership fence. `docs/architecture/README.md` is a separate presence-only check:
its title and directory-list render inputs are not recorded in the manifest.

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
  files) and drift classes for co-owned files: the schema-4
  [scaffold drift command](scaffold-drift.md). `plan` is its docs-projection library
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
