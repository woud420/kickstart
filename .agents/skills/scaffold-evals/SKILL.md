---
name: scaffold-evals
description: Run kickstart's scaffold-shape and generated-make-test evals after generator, layout, or template wiring changes, and report results by failure class.
---

# Scaffold Evals

## Use When

Use this skill after changing generators, layouts, template plans, language
setup plans, stack defaults, or templates — anything that alters generated
output. `make check` proves the code is healthy; these evals prove the
generated projects are. Full context: `docs/evals.md`.

## Scaffold Shape

Generate the supported project matrix and verify generation succeeds:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/scaffold_matrix_eval.py \
  --count 500 \
  --seed 6149 \
  --max-components-per-project 15 \
  --max-system-depth 2 \
  --exclude-known-gaps \
  --output-root /private/tmp/kickstart-scaffold-matrix-supported \
  --report /private/tmp/kickstart-scaffold-matrix-supported.md
```

Expected: zero failed commands on the supported matrix.

## Generated Project Validation

Run generated `make test` targets against the matrix output:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/generated_make_test_eval.py \
  --output-root /private/tmp/kickstart-scaffold-matrix-supported \
  --target test \
  --dependency-mode cached \
  --cache-root /private/tmp/kickstart-eval-cache \
  --report /private/tmp/kickstart-generated-make-test-supported.md \
  --timeout-seconds 90 \
  --workers 12 \
  --prewarm \
  --prewarm-workers 2
```

May need network access when dependencies are not cached. The dependency
cache is a performance tool, not part of generated behavior.

## Rules

- Write reports to scratch paths such as `/private/tmp`. Never commit
  reports, generated matrices, or caches.
- Classify failures (template wiring vs dependency vs toolchain) instead of
  compressing them into one pass/fail number. Dependency and toolchain
  flakes (for example Bun concurrent-install `EEXIST`) are environment
  issues, not template regressions — say which is which.
- A smaller `--count` is fine for a quick signal during iteration, but run
  the full supported matrix before claiming the change is validated.

## Report Back

Report projects generated, components generated, failed commands, generated
`make test` pass/fail counts, and the failure classes with one example each.
