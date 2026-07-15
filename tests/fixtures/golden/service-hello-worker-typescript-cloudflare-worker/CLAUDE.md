<!-- kickstart:begin claude-pointer -->
# CLAUDE.md

[AGENTS.md](AGENTS.md) is the canonical agent map for this repo — read it first. This file carries only Claude Code-specific wiring:

- **Skills** — `.claude/skills` is a symlink to the agent-neutral `.agents/skills/`. Add or edit skills there, never under `.claude/`. On checkouts without symlink support the link materializes as a plain text file and discovery silently degrades — read `.agents/skills/` directly.
<!-- kickstart:end claude-pointer -->
