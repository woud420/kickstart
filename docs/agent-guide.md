# Agent Guide

Purpose: kickstart generates repeatable project scaffolds so agents do not recreate setup logic from scratch.

## Generation Contract

Inputs:

- project type: `service`, `frontend`, `lib`, `cli`, `system`
- name
- root directory
- language, execution/platform profile, provider target, knowledge adapter, and extension options

Resolved metadata in `.kickstart/scaffold.json`:

- project kind and repository layout
- execution models
- runtime platforms
- emitted artifacts
- provider targets
- system composition metadata, including workspace tooling
- selected capabilities, such as implemented service extensions
- knowledge adapter
- CLI architecture metadata, including `project.architecture`, `project.cli_framework`, `project.command_root`, `project.entrypoint`, `project.operation_root`, and `project.src_root_files`

Outputs:

- directories
- rendered templates
- direct content files
- `AGENTS.md`
- `docs/architecture/`
- `docs/contracts/`
- `docs/operations/`
- `docs/decisions/`
- `.kickstart/scaffold.json`
- optional GitHub repository creation

Generated docs and `AGENTS.md` are the orientation interface for humans and agents. `.kickstart/scaffold.json` is kickstart's scaffold state, consumed by tooling (`adopt --check` today; drift reporting on the roadmap) — orientation never requires reading it.

Do not infer unsupported options. Use existing registries and typed plans.

Adoption: `kickstart adopt REPO --check --json` reports standard-artifact
gaps for repos kickstart did not create (read-only; exit 0 complete / 1
gaps / 2 usage error). Generated projects verify themselves with
`make check`; the success output names it.

## Source Of Truth

- Public API: `src/api.py`
- kickstart CLI dispatch: `src/cli/`
- Generator specs: `src/generator/specs.py`
- Directory plans: `src/generator/layouts.py`
- Managed docs projections: `src/generator/projections.py`
- Scaffold contract: `src/generator/scaffold_contract.py`
- Template plans: `src/generator/template_plans.py`
- Language setup plans: `src/generator/language_setup.py`
- Stack registry: `src/stack/`
- Templates: `src/templates/`

System generation currently lives in `src/generator/monorepo.py` and `src/templates/monorepo/` for historical compatibility. The public concept is still `system`.

Implemented service extensions are intentionally narrow. As of this contract:

- Python/FastAPI container services support `postgres`, `redis`, and `jwt`.
- Rust container services support `redis` and `jwt`.
- TypeScript container services support `postgres`.

Do not pass unsupported extension options and assume they were generated.

CLI scaffolds are modular by default for Python, Rust, and TypeScript. They expose the same conceptual boundaries in each language: command adapters, `config`, `clients`, `model`, `operations`, `output`, and `error`. Add command parsing through the generated framework: clap for Rust, Typer for Python, and oclif for TypeScript. Product behavior belongs in `src/operations`, not directly inside command adapters.

## Defaults

- service language: `python`
- service runtime: `container`
- system provider target: `multi`
- system platform profile: `kubernetes`
- system workspace tooling: `none`
- system knowledge adapter: `none`
- GitHub creation: off
- Helm: off

Use `system` for aggregate repos. `mono` and `monorepo` are legacy aliases only. Use `cloudflare-workers` as the canonical Worker runtime spelling.

Generated docs are baseline output. The `--knowledge` option only controls external metadata such as Obsidian or Backstage files.

## Safe Change Rule

Refactor only for one of two reasons:

- clearer scaffold surface for humans or agents
- risk in a weakly tested behavior path

Before changing a generator path, create or identify generated-output evidence. After changing it, prove the output did not change unless the behavior change is intentional.

## Validation

Use:

```bash
make lint
make typecheck
make tests
make check
```

The supported Python range is `>=3.12,<3.15`. Treat Python 3.12 as the compatibility floor and Python 3.14 as the current stable target.

For generator wiring changes, also use the local evals in [Local Evals](evals.md). Scaffold-shape evals should pass with zero failed commands. Generated-project dependency evals may require network and should be reported with classified failures rather than treated as invisible noise.
