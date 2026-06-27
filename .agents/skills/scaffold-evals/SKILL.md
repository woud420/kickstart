---
name: scaffold-evals
description: Runs kickstart's scaffold evals - the scaffold-shape matrix, generated make test validation, bootstrap dogfood gate, and token-savings measurement - after changes to generators, layouts, template plans, language setup plans, stack defaults, or templates, and reports results by failure class.
---

# Scaffold Evals

## Overview

Use this skill after changing generators, layouts, template plans, language
setup plans, stack defaults, or templates — anything that alters generated
output. `make check` proves the code is healthy; these evals prove the
generated projects are. Full context: `docs/evals.md`.

## Workflow

1. Run the scaffold-shape eval to generate the supported project matrix.
2. Run generated project validation (`make test`) against the same
   `--output-root` the matrix eval wrote.
3. Run the bootstrap eval — the dogfood gate — when the change touches
   templates or taste rules; iterate until consecutive clean runs.
4. Run the token-savings eval when release notes or positioning claims need
   fresh numbers.
5. Classify failures and report back (see Report Back).

## Scaffold Shape

Generate the supported project matrix and verify generation succeeds:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/scaffold_matrix_eval.py \
  --count 500 \
  --seed 6149 \
  --max-components-per-project 15 \
  --max-system-depth 2 \
  --exclude-known-gaps \
  --output-root /tmp/kickstart-scaffold-matrix-supported \
  --report /tmp/kickstart-scaffold-matrix-supported.md
```

Expected: zero failed commands on the supported matrix.

## Generated Project Validation

Run generated `make test` targets against the matrix output:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/generated_make_test_eval.py \
  --output-root /tmp/kickstart-scaffold-matrix-supported \
  --target test \
  --dependency-mode cached \
  --cache-root /tmp/kickstart-eval-cache \
  --report /tmp/kickstart-generated-make-test-supported.md \
  --timeout-seconds 90 \
  --workers 12 \
  --prewarm \
  --prewarm-workers 2
```

May need network access when dependencies are not cached. The dependency
cache is a performance tool, not part of generated behavior.

## Bootstrap (kickstart-like)

The dogfood gate: generate a kickstart-like project (typed modular CLI plus
the other supported kinds), audit taste rules (file-length cap, at most 3
directory levels below `src/`, no `Any`/`object`/`any`, specific errors,
no panic paths), and run each generated project's own `make check` to
green:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/bootstrap_eval.py \
  --output-root /tmp/kickstart-bootstrap-eval \
  --cache-root /tmp/kickstart-eval-cache \
  --report /tmp/kickstart-bootstrap-eval.md
```

Non-zero exit means a case failed generation, taste, capability-test
coverage (every manifest capability needs a generated test), or check —
fix the template, rerun, and stop iterating only after consecutive clean
runs. CI gates four cases per PR; the Scheduled Evals workflow runs the
full matrix weekly against live toolchains.

## Token Savings

Quantify how many output tokens scaffolding saves an agent versus authoring
the files by hand (useful for release notes and positioning claims):

```bash
PYTHONPATH=$(pwd) poetry run python scripts/token_savings_eval.py \
  --output-root /tmp/kickstart-token-savings \
  --report /tmp/kickstart-token-savings.md
```

Report the per-scaffold and aggregate savings ratios and state the
bytes-per-token heuristic; pass `--json` for machine-readable output.

## Validation

The eval run succeeded — and the change is validated — when:

- Scaffold shape: zero failed commands on the supported matrix; the report
  at `/tmp/kickstart-scaffold-matrix-supported.md` lists projects and
  components generated.
- Generated `make test`: the report gives pass/fail counts and every failure
  carries a class (template wiring vs dependency vs toolchain).
  Template-wiring failures are regressions; dependency and toolchain flakes
  are environment issues.
- Bootstrap: the script exits zero; non-zero means a case failed generation,
  taste, capability-test coverage, or `make check`. Done only after
  consecutive clean runs.
- Token savings: the report contains per-scaffold and aggregate ratios plus
  the bytes-per-token heuristic (`--json` for machine-readable output).
- `git status` stays clean — reports, matrices, and caches live under
  scratch paths such as `/tmp`, never in the repo.

## Anti-Patterns

- Committing reports, generated matrices, or caches. Write reports to
  scratch paths such as `/tmp`.
- Compressing failures into one pass/fail number instead of classifying
  them (template wiring vs dependency vs toolchain). Dependency and
  toolchain flakes (for example Bun concurrent-install `EEXIST`) are
  environment issues, not template regressions — say which is which.
- Claiming the change is validated from a reduced `--count` run. A smaller
  `--count` is fine for a quick signal during iteration, but run the full
  supported matrix before claiming the change is validated.
- Quoting stale token-savings numbers instead of re-running the eval.
- Stopping the bootstrap loop after a single clean run — stop iterating
  only after consecutive clean runs.

## Report Back

Report projects generated, components generated, failed commands, generated
`make test` pass/fail counts, and the failure classes with one example each.
