# Contributing

kickstart should stay small, typed, and easy to inspect.

## Principles

- Prefer explicit typed plans over long inline argument lists or dictionaries.
- Keep generators as orchestration, not data dumps.
- Keep defaults minimal. Optional systems should be opt-in.
- Preserve generated output unless the change is intentionally behavioral.
- Add tests before refactoring weakly covered paths.

## Workflow

1. Run the current tests.
2. Make the smallest source change that solves the problem.
3. Run the same tests again.
4. For generator changes, compare generated output before and after.
5. Commit source and test changes intentionally.

## Updating committed golden fixtures

The TypeScript Cloudflare Worker scaffold has a committed golden fixture at:

- `tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker`
- validated by `tests/integration/test_scaffold_golden.py`

When intentional generator changes affect this scaffold, regenerate and review the fixture diff:

```bash
tmpdir=$(mktemp -d)
poetry run kickstart create service hello-worker --lang typescript --runtime cloudflare-workers --root "$tmpdir"

rm -rf tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker
mkdir -p tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker
cp -R "$tmpdir/hello-worker/." tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker/

PYTHONPATH=$(pwd) poetry run pytest tests/integration/test_scaffold_golden.py
```

Keep fixture updates in the same commit as the generator change that required them.

## Test Commands

```bash
make lint
make typecheck
make tests
make check
```

Use `make package` to build the wheel/source distribution and `make binary` to build the local kickstart binary (a PyInstaller `--onedir` payload under `dist/kickstart/`).
GitHub Actions tests Python 3.12, 3.13, and 3.14 on Linux and macOS, then release builds attach Linux/macOS x64 and arm64 binary archives (`kickstart-<platform>-py<minor>.tar.gz`) for each supported Python minor.

## Releases

Release tags must be stable semantic versions like `v0.4.1`, and the tag must match `[project].version` in `pyproject.toml`.

Run `make release-check TAG=v0.4.1` before pushing a release tag.

Use a new patch/minor/major version for behavior or installable output changes. For docs, website copy, tests, or other same-version fixes, retag the current release line after merge so CI updates the existing GitHub Release instead of creating a new version. On reused tags, GitHub Release assets are overwritten while PyPI publish skips already-existing package artifacts for that version.

See [Release Policy](release-policy.md) for the full contract.

## Where To Add Things

- New project directories: `src/generator/layouts.py`
- New template mappings: `src/generator/template_plans.py` or `src/stack/templates.py`
- New stack choices: `src/stack/defaults.py`
- New language setup files: `src/generator/language_setup.py`
- New rendered files: `src/templates/`
