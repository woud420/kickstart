# Adoption Tiers

Checked: 2026-07-15

`kickstart adopt --check [--json]` reports a repository against the scaffold
standard at two levels. A repo is judged at the highest level it claims: no
manifest → judged at Level 1; manifest present → judged at Level 2.

## Level 1 — conformant

The vendor-neutral interface any repo can adopt with any tooling, and the
level the standard evangelizes: `AGENTS.md`, `README.md`, a Makefile exposing
the canonical `check` verb, `.agents/skills/`, the
`docs/{architecture,contracts,operations,decisions}/` skeleton, and
`.github/workflows/`. `.kickstart/scaffold.json` is deliberately not part of
this level — a repo without it can be fully conformant (exit 0).

## Level 2 — managed

Level 1 plus kickstart state that makes the repo verifiable and reconcilable:

- a valid `.kickstart/scaffold.json` (parseable, schema-shaped, able to drive
  the docs projections), and
- fence-managed docs: every managed projection target exists with its
  ownership fence (`kickstart plan` statuses `in-sync`, `presence-only`, or
  `content-drift`; content drift does not change the achieved conformance level).

The manifest is adoption payoff — it enables `kickstart plan` today and the
roadmapped drift/reconcile — never a precondition for conformance. The write
path that promotes Level 1 → Level 2 (insert fences, infer the manifest)
belongs to `kickstart adopt`'s future apply mode.

## Recorded drift

A valid manifest also produces the shared [scaffold drift report](scaffold-drift.md).
Recorded findings make `complete` false and exit 1 independently of the achieved
conformance level. Without ownership, adoption preserves its conformance result
and explicitly reports unavailable drift coverage. Use `kickstart drift` when CI
requires a recorded scope. This check does not infer ownership or write files.

## Exit codes and JSON

Exit 0 when the claimed level is fully satisfied and no recorded drift exists;
1 when recorded drift or any gap exists at
the claimed level (including a repo whose manifest claims managed but whose
docs are pre-fence); 2 for usage errors. Anything occupying the manifest path
— including a directory or broken symlink — counts as a managed claim.
`--json` emits `{"root", "complete", "achieved_level", "claimed_level",
"artifacts": [{"path", "present", "issue", "level"}], "drift"}` — Level 2 adds the
manifest status and, when the manifest itself is healthy, one
`managed docs fences` readiness entry naming any unmanaged targets (a broken
manifest is reported as a single gap, not two). For structured per-target
readiness, consume `kickstart plan --json` — adoption deliberately summarizes
it.

Pre-fence scaffolds (generated before ownership fences existed) with a
manifest report `not fence-managed` gaps by design: re-render the managed
docs with a current kickstart or wait for the adopt write path.
