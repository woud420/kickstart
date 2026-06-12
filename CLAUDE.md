# CLAUDE.md

Project guidance lives in [AGENTS.md](AGENTS.md): the source-of-truth map,
current scaffold model, change rules, validation commands, and release
process. Read it first; this file only adds Claude Code specifics.

## Skills

Repo skills are agent-neutral and live in [`.agents/skills/`](.agents/skills/).
`.claude/skills` is a symlink to that directory, so Claude Code discovers
them natively. Add or edit skills under `.agents/skills/`, never under
`.claude/` directly.

Note: on checkouts without symlink support (Windows without Developer Mode,
`core.symlinks=false`, ZIP exports) the symlink materializes as a plain text
file and skill discovery silently degrades — read skills from
`.agents/skills/` directly in that case.

## Quick verification

```bash
make check                      # lint, typecheck, hygiene audits, tests
cd website && bun run check     # website typecheck + tests
make release-check TAG=vX.Y.Z   # release tag policy (docs/release-policy.md)
```

For generator or template wiring changes, run the evals in
[docs/evals.md](docs/evals.md) and report failure classes, not just totals.
