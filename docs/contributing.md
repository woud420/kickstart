# Contributing

Kickstart should stay small, typed, and easy to inspect.

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

## Test Commands

```bash
make lint
make typecheck
make tests
make check
```

Use `make package` to build the wheel/source distribution and `make binary` to build the local standalone binary.
GitHub Actions tests Python 3.12, 3.13, and 3.14 on Linux and macOS, then release builds attach Linux/macOS x64 and arm64 binaries for each supported Python minor.

## Where To Add Things

- New project directories: `src/generator/layouts.py`
- New template mappings: `src/generator/template_plans.py` or `src/stack/templates.py`
- New stack choices: `src/stack/defaults.py`
- New language setup files: `src/generator/language_setup.py`
- New rendered files: `src/templates/`
