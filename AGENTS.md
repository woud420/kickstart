# Agent Map

Purpose: kickstart generates deterministic starter repos for humans and coding agents. Keep the scaffold contract explicit, typed, and easy to review.

## Source Of Truth

- Public API: `src/api.py`
- CLI parsing and dispatch: `src/cli/`
- Explicit export commands: `src/cli/exports.py`; external I/O data/validation: `src/generator/external_io_*.py`
- Generator specs: `src/generator/specs.py`
- Directory plans: `src/generator/layouts.py`
- Managed docs projections: `src/generator/projections.py`
- Ownership fences: `src/generator/markers.py`
- Docs drift plan: `src/generator/docs_plan.py`
- Persisted ownership plan and bounded inspection: `src/generator/ownership_plan.py`, `src/generator/ownership_check.py`
- Classed scaffold drift and CI structural checks: `src/generator/drift.py`, `src/generator/workflow_check.py`
- Backstage export: `src/generator/backstage_export.py`
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
- Claude Code wiring: the Claude Code section below (`CLAUDE.md` only imports this file)

## Current Model

- Primary project types: `service`, `frontend`, `lib`, `cli`, and `system`.
- `system` is the primary aggregate repo. `mono` and `monorepo` are legacy aliases.
- Service runtimes are `container` and `cloudflare-workers`.
- Manifest readers accept 3.0, 3.1, 3.2 and 4.0; fresh generation emits 4.0 after the tested explicit `migrate` path. Schema 4.0 represents Workers as service execution profiles.
- Cloudflare Workers are not Docker containers. Cloudflare Containers are reserved for future support.
- Fresh schema-4 manifests persist per-file ownership. `plan --ownership` inspects recorded fences and structural facts; migration leaves historical ownership unrecorded.
- Generated docs and `.kickstart/scaffold.json` are baseline output. `--knowledge` only controls external Obsidian/Backstage metadata.

## Change Rules

- Prefer typed dataclasses and explicit plans over untyped dictionaries.
- Keep generators as orchestration; move repeated data into layouts, template plans, language setup plans, or stack defaults.
- Refactor only for human/agent clarity or to address a weakly tested path.
- Do not change generated behavior accidentally. If behavior changes, update tests and say so.
- Do not commit local reports, scratch files, or idea notes.

## Validation

Run the aggregate gate once for the source state being verified; it includes lint,
typecheck, and tests. Use individual targets during iteration.

```bash
make check
```

For website changes, also run:

```bash
cd website && bun run check
```

For generator wiring changes, also run the evals in `docs/operations/evals.md` and report both command output and failure classes (see the `scaffold-evals` skill).

## Releases

Follow `docs/release-policy.md` (see the `cut-release` skill):

- Bump `pyproject.toml` and `src/__init__.py:__version__` together; `make release-check TAG=vX.Y.Z` fails when they disagree.
- Add the release entry to `CHANGELOG.md` and `website/src/site/content.ts`; website tests fail when the current version has no release note.
- Open each `CHANGELOG.md` version section with a one-paragraph summary. `ci/release_notes.py` puts it at the top of the GitHub Release page, and the release job fails without it.
- Keep website release notes to a title, one sentence, and at most three plain-language highlights; the details belong in `CHANGELOG.md`.
- Release tags are stable semver only (`vX.Y.Z`), tagged on `master` after merge.

## Skills

Reusable agent workflows live in `.agents/skills/`, one directory per skill with a `SKILL.md`:

- `kickstart`: scaffold projects with the installed `kickstart` binary.
- `cut-release`: cut, tag, and verify a kickstart release.
- `scaffold-evals`: run the scaffold-shape, generated-`make test`, and token-savings evals and report failure classes.
- `backstage-catalog`: derive `catalog-info.yaml` from `.kickstart/scaffold.json` for Backstage registration.
- `website-update`: update kickstart-cli.org content against the tests that enforce it.

Keep skills agent-neutral and add new ones under `.agents/skills/`.

## Claude Code

`CLAUDE.md` only imports this file. The Claude-specific wiring:

- Skills are discovered through the `.claude/skills` symlink to `.agents/skills/`. Edit skills there, never under `.claude/`. Where symlinks are unsupported (Windows without Developer Mode, `core.symlinks=false`, ZIP exports) the link is a plain file, so read `.agents/skills/` directly.
- Hooks live in `.claude/hooks/` and are registered in `.claude/settings.json`, for example `session-start.sh`, which installs Python and website dependencies in the web sandbox. Hooks have no cross-vendor standard, so they stay under `.claude/`.
