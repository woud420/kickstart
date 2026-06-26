# CLAUDE.md

[AGENTS.md](AGENTS.md) is the source of truth for this repo — the map, scaffold
model, change rules, validation commands, and release process. Read it first;
everything that applies to any agent lives there.

This file carries only Claude Code-specific wiring:

- **Skills** — the agent-neutral skills in [`.agents/skills/`](.agents/skills/)
  are discovered through the `.claude/skills` symlink. Add or edit skills under
  `.agents/skills/`, never under `.claude/`. On checkouts without symlink
  support (Windows without Developer Mode, `core.symlinks=false`, ZIP exports)
  the symlink materializes as a plain text file and discovery silently
  degrades — read `.agents/skills/` directly.
- **Hooks** — Claude Code-specific hooks live in `.claude/hooks/`, registered in
  `.claude/settings.json` (e.g. the sandbox `session-start.sh`, which bootstraps
  Python + website dependencies on session start). Hooks have no cross-vendor
  standard, so they stay under `.claude/` rather than the neutral `.agents/`.
