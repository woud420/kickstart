# Local Evals

One entrypoint runs the suite by tier (see
`docs/decisions/headroom-benchmark-learnings.md` for where this design
comes from):

```bash
PYTHONPATH=$(pwd) poetry run python scripts/run_evals.py --tier smoke   # headline bootstrap case
PYTHONPATH=$(pwd) poetry run python scripts/run_evals.py --tier pr      # what CI gates per PR + weight baselines
PYTHONPATH=$(pwd) poetry run python scripts/run_evals.py --tier full    # full matrix + tokens + determinism + website
```

Individual evals below remain directly runnable for iteration; do not rerun them
after a passing tier already covered the same inputs. Reuse successful results
while generator, template, fixture, toolchain, and dependency inputs are unchanged.
Rerun affected checks after a relevant fix; repeat unchanged clean runs only to
investigate nondeterminism or satisfy a specific eval's repetition contract.
State the completed tier and coverage when reporting results. The full supported
matrix is still required for a claim of full validation, and releases retain their
full-tier gate.

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

Expected result for the supported matrix is zero failed commands. The dated
2026-10-17 UTC snapshot generated **500 projects / 4,696 components**, with
**0 failed commands and 0 component issues**. It used seed 6149, a maximum of 15
components per project, depth 2 and known gaps excluded. The exact `build_plans`
output was evaluated in four isolated output shards by
`PYTHONPATH=$(pwd) poetry run python /tmp/eng557-matrix.py`.

Generation ran at `39a5b1d56b94d5831ee75125f725e8312e0f9a30`; its `src` tree is
identical to published master `c71c6df8e553a762031034fbbee5228c041ac200`.
Reports: `/tmp/eng557-scaffold-matrix.md` and
`/tmp/eng557-scaffold-matrix.json`; exact root and input provenance:
`/tmp/eng557-generation-provenance.json`. This snapshot covers those published
generator inputs; unmerged feature profiles require their own verification.

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
  --prewarm-workers 2 \
  --clean-completed
```

This eval may need network access when dependencies are not already cached.
The dependency cache is a performance tool, not part of generated behavior.
Inventory is based on Makefiles beside `.kickstart/scaffold.json`, so installed
dependencies' unrelated Makefiles do not become extra scaffold targets. An empty
inventory is a usage error.

The example opts into `--clean-completed` for a large scratch matrix; the default
is false. After a leaf target exits, this removes real local `.venv`,
`node_modules` and `.cache` directories, preserving symlinks, aggregate roots,
shared caches and directories containing recorded source paths. Removal errors
become per-component cleanup warnings, separate from make-test verdicts.

The evaluator writes `<report>.json` alongside the Markdown report. Both retain
one run ID, dates, source revision/dirty state, command, tool versions, dependency
mode, prewarm results and per-component outcomes. Each file is replaced
atomically; the pair is not a cross-file transaction, so verify matching run IDs.
Console totals appear only after both files persist. A completed report retains
the existing report-only exit status **0 even when component targets fail**;
inspect `failed`, `by_reason`, prewarm failures and cleanup warnings.

### Dated runtime snapshot: 2026-10-17

The completed run recorded **4,595 passed / 101 failed out of 4,696 targets**;
prewarm passed **21/21**, with zero prewarm failures. Runtime source was clean
`e6c672bfcf14345d8ba97861b6f2081e2fbd4cba`, using the same generator inputs as
the shape snapshot above.

| Context | Recorded value |
|---|---|
| Run window | 2026-10-17 08:16:15–08:37:46 UTC |
| Run ID | `5c9dbbbc-87d5-458e-89cc-a5a58a1ceebe` |
| Host | macOS 15.6, arm64 |
| Dependency mode | Cached, network enabled; warm retry after incomplete attempts |
| Parallelism | 12 target workers, 90-second target timeout; 2 prewarm workers |
| Cleanup | Enabled; 2,396 components cleaned, 1 component with a retained warning |
| Python / Poetry | Python 3.14.8 / Poetry 2.5.1 |
| JavaScript | Bun 1.3.5 / Node v26.11.1 |
| Rust / Go | Cargo and rustc 1.99.0 / Go 1.27.2 |
| Build tools | CMake 4.4.4 / GNU Make 3.81 |

The exact command, output/cache roots and complete version strings are retained
in `/tmp/eng557-final-generated-make-test.md.json` and
`/tmp/eng557-final-runtime-start.json`. Markdown:
`/tmp/eng557-final-generated-make-test.md`; matching console summary:
`/tmp/eng557-final-generated-make-test.log`. Read-back and hashes:
`/tmp/eng557-runtime-proof.json`. The JSON report SHA-256 is
`3786b39ac5456f7680db69a9b05b0a3f1a7126b11e49758edcd81cd055e5888f`.
All 134,160 recorded scaffold source entries remained unchanged
(`/tmp/eng557-generated-source-final.json`).

Raw classifier totals are **99 `other failure`** and
**2 `node test dependency missing`**. Retained output tails support this finer
symptom breakdown; these are execution symptoms, not proven root causes:

| Observed symptom | Targets | Interpretation |
|---|---:|---|
| Bun install `EEXIST` | 34 | Dependency linking/symlink conflict |
| Other Bun install failures | 45 | Install blocker; cause absent from retained tail |
| Third-party module path in test startup failure | 11 | Dependency/startup symptom; cause truncated |
| Node 26 test startup failure | 9 | Unresolved startup failure; cause truncated |
| Missing `vitest` command | 2 | Test dependency unavailable |

Five serialized, warm-cache representative retries passed three cases (one each
from the install-conflict, unspecified-install and missing-command groups). Two
still failed with `ERR_MODULE_NOT_FOUND` in Vitest/Rollup dependencies. Full
retry logs and the symptom mapping are listed in
`/tmp/eng557-failure-classification.json`. These retries do not replace the
original 101 failures or prove all failures are external. No separate network or
compiler/toolchain failure class was identified from the retained tails; no
individual scaffold assertion defect was isolated. Further dependency/workspace
investigation remains necessary; this is not a claim that the full generated
runtime matrix is green.

Two earlier attempts on 2026-10-17 have **unknown runtime totals**: raw retention
was stopped at 07:33 UTC before disk exhaustion
(`/tmp/eng557-first-attempt-stop.json`); the first bounded retry failed report
collection at 08:11 UTC after a cleanup `ENOTEMPTY` exception
(`/tmp/eng557-bounded-attempt-failure.json`). The completed run above includes
the tested repair that retains cleanup warnings without losing make results.
The older 2026-10-15 ENOSPC attempt also lacks completed runtime proof. None of
these incomplete attempts supplies current pass/failure counts.

When reporting this eval, include the date, source, context, pass count, prewarm
results, cleanup warnings and failure classes. Do not compress failures into a
single success flag or reuse undated totals.

### Bun workspace coordination: 2026-10-17

The evaluator groups a generated Bun workspace's root and declared members into
one serial task, including each target's cleanup. Separate workspaces,
standalone packages, nonmembers and nested workspaces retain their own parallel
slots. Runtime and prewarm use the same scheduling policy. This coordination
applies within one evaluator invocation.

The controlled reproduction uses `create system` with explicit
`--workspace-tooling bun-turbo`, a TypeScript Worker and a React frontend under
`apps/`. A neutral system root leaves those apps independent and cannot exercise
shared-workspace installation. Each configuration below has three independent
repetitions and two targets per workspace. All warm setup installs passed; each
case had a private cache. Before source was clean `e048a6d`; after source was
clean `fdff607`. Bun was **1.3.5**, Node **v26.11.1**, on the same macOS host.
All 48 Bun lockfiles are byte-identical across the before/after cases
(`/tmp/eng635-control-dependency-locks.json`), excluding a resolved-version
change as the explanation for the result.

| Dependency tree | Workers requested | Cleanup | Before pass/fail | After pass/fail |
|---|---:|---|---:|---:|
| Fresh | 1 | Off | 6/0 | 6/0 |
| Fresh | 1 | On | 6/0 | 6/0 |
| Fresh | 2 | Off | 6/0 | 6/0 |
| Fresh | 2 | On | 6/0 | 6/0 |
| Warm | 1 | Off | 6/0 | 6/0 |
| Warm | 1 | On | 6/0 | 6/0 |
| Warm | 2 | Off | 0/6 | 6/0 |
| Warm | 2 | On | 1/5 | 6/0 |

The 11 before-repair failures occur during `bun install`, before generated tests
start. They reproduce with cleanup off. All **48/48** after-repair targets pass.
Two independent warm workspaces sharing one cache also pass **6/6** targets,
with actual command overlap in all three repetitions. Additional nested-member
workspace controls pass **6/6** across three independent generated workspaces
(`/tmp/eng635-nested-member-proof.json`). The network-free
regressions exercise runtime, prewarm, root targets, cleanup ordering,
membership, nested boundaries and malformed metadata. Five overlap/cleanup
controls fail before repair; all 30 focused runner/reporting checks pass after,
with 100% executable-line coverage in the workspace grouping module.

Detailed control logs and source checks are indexed by
`/tmp/eng635-workspace-proof.json` and `/tmp/eng635-workspace-proof.md`.
The earlier neutral-system comparison passed 72/72 standalone targets; it is
not a shared-workspace reproduction. The initial sandboxed workspace run was
registry-blocked, including warm setup, and supplies no concurrency conclusion.

#### Fresh full runtime comparison

A new exact supported matrix generated **500 projects / 4,696 components** with
zero generation failures or component issues. Generator tree
`74bddecce6a8b4300f7ee6c49b362d79b024cafe` matches `master` at `c71c6df` and the earlier
snapshot. From clean evaluator source
`fdff607bdfc736f1cb833440def6262bedb6b158`, all **4,696/4,696** runtime targets pass;
prewarm passes **21/21**. No component or prewarm failure class was observed in
this run. Native `make check` passes **1,100 tests**.

| Context | Recorded value |
|---|---|
| Run window | 2026-10-17 09:20:55–09:43:14 UTC |
| Run ID | `b77f1a7f-bb89-473d-82b7-23ab0fad0890` |
| Dependencies | Fresh generated trees; existing warm shared package/build caches; network enabled |
| Parallelism | 12 workers; 90-second target timeout; 2 prewarm workers |
| Cleanup | Enabled; 2397 components cleaned; 0 components with warnings |
| JavaScript | Bun 1.3.5 / Node v26.11.1 |
| Host and other tools | Same recorded host/toolchain as the earlier snapshot; full versions in JSON |

The actual CLI command and source/tool provenance are in
`/tmp/eng635-final-generated-make-test.md.json`; Markdown:
`/tmp/eng635-final-generated-make-test.md`; console:
`/tmp/eng635-final-generated-make-test.log`. Both report files and console totals
were read back against the exact 4,696-target inventory. JSON SHA-256:
`94177050f1c28f5c94b7a048307f924301d13516fe56dac7481e0e8cb2941bd3`. All **134,160** recorded scaffold source entries remain unchanged
(`/tmp/eng635-generated-source-final.json`); their initial fingerprints also
match the earlier matrix exactly (`/tmp/eng635-cross-run-scaffold-equality.json`).
Shape and command context:
`/tmp/eng635-generation-provenance.json` and
`/tmp/eng635-final-runtime-start.json`.

The original 4,595/101 warm-retry snapshot above retains its original hashes and
counts. Inspection of two persistent startup examples found missing installed
Vitest/Rollup files with intact shared-cache copies
(`/tmp/eng635-retained-store-inspection.json`). The scheduler prevents overlapping
workspace targets; it does not repair an already damaged dependency store or
identify the cause of every historical startup symptom. After an interrupted
evaluation, generate a fresh matrix into a new owned output root for a clean
dependency-tree comparison. Preserve the earlier report and label cache warmth
separately from the generated tree's install state.

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

The default bootstrap matrix is the `DEFAULT_CASES` registry in
[`scripts/bootstrap_eval.py`](../../scripts/bootstrap_eval.py). Each record
includes the scaffold arguments that define the case. Use `--cases` to select
a subset. Beyond the taste rules, every
capability declared in `.kickstart/scaffold.json` must be exercised by at
least one generated test (`capability-tests` rule). The eval exits non-zero
when any case fails generation, taste, capability coverage, or `make check`.

CI runs `run_evals.py --tier pr` on every PR.
[`scripts/run_evals.py`](../../scripts/run_evals.py) defines `TIERS` and
`_PR_BOOTSTRAP_CASES`, including the bootstrap selection and additional checks
for each tier. The `Scheduled Evals` workflow runs `--tier full` weekly
against live toolchains.

The full matrix includes a Go service and a frontend; each runs its own generated `make check`,
including tests. The weekly workflow reads the Go version from the generator's
toolchain registry and installs it explicitly. Go sources participate in the
common file-size and depth audits; TSX sources use the same TypeScript pattern
rules as TS. These audits remain bounded heuristics, with failures reported by
rule rather than exempting cases.

Bootstrap coverage is limited to the registered cases: a supported scaffold
without a case is not exercised by that gate. Add new cases to the executable
registry and choose their tier explicitly; keep the fast PR selection separate
from the full weekly matrix.

## Scaffold Weight Baselines

`tests/fixtures/scaffold-weight-baselines.json` pins each scaffold's file
count and content bytes. `token_savings_eval.py --check-baselines` fails
when a scaffold's file count changes at all or its bytes drift beyond
±10% of the committed baseline — the regression guard for the
token-efficiency promise, run per PR (tier `pr`) and weekly (tier `full`):

```bash
PYTHONPATH=$(pwd) poetry run python scripts/token_savings_eval.py --check-baselines
PYTHONPATH=$(pwd) poetry run python scripts/token_savings_eval.py --update-baselines  # acknowledge deliberate changes
```

Re-baseline (`--update-baselines`) only for deliberate template changes,
and commit the fixture diff in the same PR as the template change so the
review sees the weight delta.
