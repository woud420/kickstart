# Agent Map

Purpose: kickstart generates deterministic starter repos for humans and coding agents. Keep the scaffold contract explicit, typed, and easy to review.

## Source Of Truth

- Public API: `src/api.py`
- CLI parsing and dispatch: `src/cli/`
- Generator specs: `src/generator/specs.py`
- Directory plans: `src/generator/layouts.py`
- Template plans: `src/generator/template_plans.py`
- Language setup plans: `src/generator/language_setup.py`
- Scaffold metadata: `src/generator/scaffold_contract.py`
- Stack registry and defaults: `src/stack/`
- Templates: `src/templates/`
- System generator/templates currently use historical `monorepo` file paths.
- Website: `website/`
- Docs: `docs/`
- Changelog: `CHANGELOG.md` (mirrored on the website by `website/src/site/content.ts`)
- Release policy: `docs/release-policy.md`, enforced by `ci/release_policy.py`
- Agent skills: `.agents/skills/` (`.claude/skills` is a symlink to it)
- Agent daemons: `.agents/daemons/`
- Agent hooks: `.agents/hooks/` (vendor-neutral scripts; Claude wires them in via `.claude/settings.json`, e.g. the sandbox `session-start.sh`)

## Current Model

- Primary project types: `service`, `frontend`, `lib`, `cli`, and `system`.
- `system` is the primary aggregate repo. `mono` and `monorepo` are legacy aliases.
- Service runtimes are `container` and `cloudflare-workers`.
- Cloudflare Workers are not Docker containers. Cloudflare Containers are reserved for future support.
- Generated docs and `.kickstart/scaffold.json` are baseline output. `--knowledge` only controls external Obsidian/Backstage metadata.

## Change Rules

- Prefer typed dataclasses and explicit plans over untyped dictionaries.
- Keep generators as orchestration; move repeated data into layouts, template plans, language setup plans, or stack defaults.
- Refactor only for human/agent clarity or to address a weakly tested path.
- Do not change generated behavior accidentally. If behavior changes, update tests and say so.
- Do not commit local reports, scratch files, or idea notes.

## Validation

Use:

```bash
make lint
make typecheck
make tests
make check
```

For website changes, also run:

```bash
cd website && bun run check
```

For generator wiring changes, also run the evals in `docs/evals.md` and report both command output and failure classes (see the `scaffold-evals` skill).

## Releases

Follow `docs/release-policy.md` (see the `cut-release` skill):

- Bump `pyproject.toml` and `src/__init__.py:__version__` together; `make release-check TAG=vX.Y.Z` fails when they disagree.
- Add the release entry to `CHANGELOG.md` and `website/src/site/content.ts`; website tests fail when the current version has no release note.
- Release tags are stable semver only (`vX.Y.Z`), tagged on `master` after merge.

## Skills

Reusable agent workflows live in `.agents/skills/`, one directory per skill with a `SKILL.md`:

- `kickstart`: scaffold projects with the installed `kickstart` binary.
- `cut-release`: cut, tag, and verify a kickstart release.
- `scaffold-evals`: run the scaffold-shape, generated-`make test`, and token-savings evals and report failure classes.
- `backstage-catalog`: derive `catalog-info.yaml` from `.kickstart/scaffold.json` for Backstage registration.
- `website-update`: update kickstart-cli.org content against the tests that enforce it.

`.claude/skills` is a symlink to `.agents/skills` so Claude Code discovers the same skills natively. Keep skills agent-neutral and add new ones under `.agents/skills/`.

## Agent assets convention

Vendor-neutral agent assets live under `.agents/` (`skills/`, `daemons/`, `hooks/`); vendor-specific wiring is a thin shim on top, anchored by the cross-tool `AGENTS.md` standard:

- **Instructions**: `AGENTS.md` is the source of truth; `CLAUDE.md` is a thin pointer to it.
- **Skills**: content in `.agents/skills/`; `.claude/skills` symlinks to it (Claude discovers skills by directory scan).
- **Hooks**: scripts in `.agents/hooks/`; `.claude/settings.json` registers them by path (hooks are not directory-scanned, so no symlink is needed). The hook contract itself (event names, `CLAUDE_*` env vars) is Claude-specific; another runner reuses the same script from its own config.
