# Local Evals

kickstart has two useful local eval layers:

- Scaffold shape: generate many supported project combinations and verify the generator commands succeed.
- Generated project validation: run generated `make test` targets to catch template wiring, dependency, and toolchain issues.

Reports should be written to scratch paths such as `/private/tmp`. Do not commit reports.

## Scaffold Shape

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

Expected result for the supported matrix is zero failed commands. The most recent local run generated 500 projects and 4696 components with 0 failed commands.

## Generated Project Validation

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

This eval may need network access when dependencies are not already cached. The dependency cache is a performance tool, not part of generated behavior.

The most recent local cached-network run validated 4696 generated Makefiles: 4589 passed and 107 failed. The prewarm phase passed 21 of 21 targets. Remaining failures were classified into dependency, install, and toolchain failure classes, mostly Bun concurrent install/cache `EEXIST` errors and `workerd` install failures under Node 25.

When reporting this eval, include the pass count and the failure classes. Do not compress failures into a single pass/fail number.

## Token Savings

kickstart's value to agents includes replacing thousands of hand-authored
boilerplate tokens with one short command. Measure it:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/token_savings_eval.py \
  --output-root /private/tmp/kickstart-token-savings \
  --report /private/tmp/kickstart-token-savings.md
```

The eval generates representative scaffolds (service, worker, CLI, library,
system), counts the UTF-8 text content an agent would otherwise emit, and
estimates tokens at ~4 bytes per token. The most recent local run measured a
208x aggregate saving: ~17,500 output tokens of generated starter files
versus ~84 tokens of `kickstart create` commands (135x-288x per scaffold).

Pass `--json` for machine-readable results. The heuristic is intentionally
model-agnostic; report bytes alongside tokens when precision matters.

## Bootstrap (kickstart-like) Eval

The dogfood standard: kickstart must bootstrap a project shaped like
kickstart itself — a typed, modular CLI with docs, tests, and canonical Make
verbs — that is green with no manual fixes. Each case is generated, audited
against the taste rules (<= 200 lines per source file, no `Any`/`object` in
Python, no `any`/`Object` in TypeScript, no `unwrap()`/`panic!` outside Rust
tests, specific exception types), then verified with the generated project's
own `make check`:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/bootstrap_eval.py \
  --output-root /private/tmp/kickstart-bootstrap-eval \
  --cache-root /private/tmp/kickstart-eval-cache \
  --report /private/tmp/kickstart-bootstrap-eval.md
```

Default cases: python CLI (the kickstart-like headline case), python lib,
python service, typescript worker, rust CLI. Use `--cases` to iterate on a
single scaffold. The eval exits non-zero when any case fails generation,
taste, or `make check`, so it can gate template changes locally.
