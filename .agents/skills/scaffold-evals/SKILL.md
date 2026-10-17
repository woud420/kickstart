---
name: scaffold-evals
description: Run kickstart's scaffold-shape and generated-make-test evals after generator, layout, or template wiring changes, and report results by failure class.
---

# Scaffold Evals

## Workflow

Run one tiered entrypoint for the scope being verified:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/run_evals.py --tier pr    # or smoke / full
```

After deliberate template weight changes, re-baseline:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/token_savings_eval.py --update-baselines
```

## Overview

Use this skill after changing generators, layouts, template plans, language
setup plans, stack defaults, or templates — anything that alters generated
output. `make check` proves the code is healthy; these evals prove the
generated projects are. Full context: `docs/operations/evals.md`.

The individual commands below are alternatives for focused iteration, not an
additional checklist after a tier already covered them. Reuse a passing result
for unchanged generator, template, fixture, toolchain, and dependency inputs.
After a relevant fix, rerun the affected checks and the required completion tier.

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
fix the template and rerun the affected checks. Repeat an unchanged clean run
only when investigating nondeterminism or when a specific eval requires it.
CI gates a fast subset per PR; the Scheduled Evals workflow runs the
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

## Anti-Patterns

- Do not commit reports, generated matrices or caches; write them to scratch
  paths such as `/tmp`.
- Do not compress template-wiring, dependency and toolchain failures into one
  pass/fail number; classify them. Dependency and toolchain
  flakes (for example Bun concurrent-install `EEXIST`) are environment
  issues, not template regressions — say which is which.
- Do not claim validation from a reduced shape sample. A smaller `--count`
  is fine during iteration; run the full supported matrix before completion.

## Validation

Report projects generated, components generated, failed commands, generated
`make test` pass/fail counts, and the failure classes with one example each.
