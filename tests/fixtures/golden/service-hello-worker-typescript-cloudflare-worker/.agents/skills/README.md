<!-- kickstart:begin agents-skills-readme -->
# Agent Skills

Repo-local agent skills live here, one directory per skill with a `SKILL.md` carrying the portable core instructions (keep any frontmatter spec-only so every agent runtime can load it).

- Add a skill: create `<skill-name>/SKILL.md` stating when to use it and the exact procedure.
- Keep skills agent-neutral; vendor-specific wiring stays with the vendor (Claude Code discovers this directory through the `.claude/skills` symlink).
- Promote a skill beyond this repo only on reuse evidence — a workflow recurring across repos, devices, or sessions; repo-specific workflows stay here.
<!-- kickstart:end agents-skills-readme -->
