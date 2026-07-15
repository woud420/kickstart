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
  `content-drift`; content drift is a plan concern, not an adoption gap).

The manifest is adoption payoff — it enables `kickstart plan` today and the
roadmapped drift/reconcile — never a precondition for conformance. The write
path that promotes Level 1 → Level 2 (insert fences, infer the manifest)
belongs to `kickstart adopt`'s future apply mode.

## Exit codes and JSON

Exit 0 when the claimed level is fully satisfied; 1 when any gap exists at
the claimed level (including a repo whose manifest claims managed but whose
docs are pre-fence); 2 for usage errors. `--json` emits `{"root",
"complete", "achieved_level", "claimed_level", "artifacts": [{"path",
"present", "issue", "level"}]}` — Level 2 adds the manifest status and one
`managed docs fences` readiness entry naming any unmanaged targets.

Pre-fence scaffolds (generated before ownership fences existed) with a
manifest report `not fence-managed` gaps by design: re-render the managed
docs with a current kickstart or wait for the adopt write path.
