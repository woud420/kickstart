# Agent Guide

Purpose: kickstart generates repeatable project scaffolds so agents do not recreate setup logic from scratch.

## Generation Contract

Inputs:

- project type: `service`, `frontend`, `lib`, `cli`, `mono`
- name
- root directory
- language, runtime, deploy, cloud, knowledge adapter, and extension options

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

Do not infer unsupported options. Use existing registries and typed plans.

## Source Of Truth

- Public API: `src/api.py`
- CLI dispatch: `src/cli/`
- Generator specs: `src/generator/specs.py`
- Directory plans: `src/generator/layouts.py`
- Scaffold contract: `src/generator/scaffold_contract.py`
- Template plans: `src/generator/template_plans.py`
- Language setup plans: `src/generator/language_setup.py`
- Stack registry: `src/stack/`
- Templates: `src/templates/`

## Defaults

- service language: `python`
- service runtime: `container`
- monorepo cloud: `multi`
- monorepo runtime: `kubernetes`
- monorepo knowledge adapter: `none`
- GitHub creation: off
- Helm: off

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
