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

For generator wiring changes, also run the evals in `docs/evals.md` and report both command output and failure classes.
