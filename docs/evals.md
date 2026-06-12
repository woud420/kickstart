# Local Evals

kickstart has two useful local eval layers:

- Scaffold shape: generate many supported project combinations and verify the generator commands succeed.
- Generated project validation: run generated `make test` targets to catch template wiring, dependency, and toolchain issues.

Reports should be written to scratch paths such as `/tmp`. Do not commit reports.

## Scaffold Shape

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

Expected result for the supported matrix is zero failed commands. The most recent local run generated 500 projects and 4696 components with 0 failed commands.

## Generated Project Validation

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

This eval may need network access when dependencies are not already cached. The dependency cache is a performance tool, not part of generated behavior.

The most recent local cached-network run validated 4696 generated Makefiles: 4589 passed and 107 failed. The prewarm phase passed 21 of 21 targets. Remaining failures were classified into dependency, install, and toolchain failure classes, mostly Bun concurrent install/cache `EEXIST` errors and `workerd` install failures under Node 25.

When reporting this eval, include the pass count and the failure classes. Do not compress failures into a single pass/fail number.

## Token Savings

kickstart's value to agents includes replacing hand-authored boilerplate
tokens with one short command. Measure it honestly:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/token_savings_eval.py \
  --output-root /tmp/kickstart-token-savings \
  --report /tmp/kickstart-token-savings.md
```

The eval generates representative scaffolds (service, worker, CLI, library,
system), counts UTF-8 text content, and estimates tokens at ~4 bytes per
token. It reports two ratios:

- **Full-output ratio (upper bound)**: assumes the agent would retype every
  generated file. Measured at v0.4.2: ~190x aggregate.
- **App-code ratio**: excludes scaffold metadata (manifest, agent map, docs
  skeleton, CI), approximating a minimal hand-written equivalent. Measured
  at v0.4.2: ~129x aggregate.

Both denominators count only the command string, not skill or tool-call
overhead, so treat ratios as comparative rather than absolute. For a truly
minimal script the honest answer is that `uv init`/`cargo new` plus a couple
of files is competitive; the savings are real when the task wants the full
production shape (tests, CI, container, docs, uniform Make verbs). Re-run
the eval rather than quoting stale numbers; pass `--json` for
machine-readable results.

## Bootstrap (kickstart-like) Eval

The dogfood standard: kickstart must bootstrap a project shaped like
kickstart itself — a typed, modular CLI with docs, tests, and canonical Make
verbs — that is green with no manual fixes. Each case is generated, audited
against the taste rules (<= 200 lines per source file, <= 3 directory levels below `src/`, no `Any`/`object` in
Python, no `any`/`Object` in TypeScript, no `unwrap()`/`panic!` outside Rust
tests, specific exception types), then verified with the generated project's
own `make check`:

```bash
PYTHONPATH=$(pwd) poetry run python scripts/bootstrap_eval.py \
  --output-root /tmp/kickstart-bootstrap-eval \
  --cache-root /tmp/kickstart-eval-cache \
  --report /tmp/kickstart-bootstrap-eval.md
```

Default cases: python CLI (the kickstart-like headline case), python lib,
python service with all extensions, typescript worker, rust CLI. Use
`--cases` to iterate on a single scaffold. Beyond the taste rules, every
capability declared in `.kickstart/scaffold.json` must be exercised by at
least one generated test (`capability-tests` rule). The eval exits non-zero
when any case fails generation, taste, capability coverage, or `make check`.

CI gates four cases on every PR (python CLI, full-extension python service,
typescript worker, rust CLI); the `Scheduled Evals` workflow runs the full
matrix plus the website-examples drift check weekly against live
toolchains, so template rot surfaces within a week without slowing PRs.
