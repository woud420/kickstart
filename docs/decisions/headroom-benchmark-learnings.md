# Headroom Benchmark Learnings

Date: 2026-06-12

Source studied: https://github.com/chopratejas/headroom — a context-compression
layer for AI agents (60–95% token reduction claims). Its `/benchmarks`
directory and published methodology carry several practices worth comparing
against kickstart's eval suite (`docs/evals.md`).

## What headroom does that we should notice

1. **Paired quality + efficiency metrics.** Headroom never reports
   compression alone; every headline pairs compression % with accuracy
   preserved on standard tasks (GSM8K 0.870 baseline maintained, SQuAD v2
   97% accuracy at 19% compression, BFCL 97% at 32%). The optimization is
   only claimed valid while the outcome metric holds.
2. **A central runner with tiers.** `python -m headroom.evals suite
   --tier 1` — one entrypoint, tier 1 cheap enough to run often, deeper
   tiers for thorough validation.
3. **Adversarial and worst-case suites as committed code.**
   `adversarial_ccr_tests.py`, `headroom_worst_case_benchmark.py` — attack
   coverage is a repeatable artifact, not a one-off review.
4. **Regression benchmarks.** `ccr_regression_benchmark.py` pins prior
   results so optimization wins cannot silently erode.
5. **Scenario fixtures separated from runner code** (`scenarios/`), with a
   single `run_benchmarks.py` harness.
6. **Real-workload case studies beside synthetic suites** (code search 92%,
   SRE debugging 92%, issue triage 73%) — synthetic benchmarks prove
   mechanism, workload studies prove relevance.
7. **Headline numbers ship with the reproduce command** in the README/docs.

## Where kickstart already stands

| Headroom practice | kickstart today |
| --- | --- |
| Paired quality+efficiency | Split across two evals: token savings (efficiency) and bootstrap eval (quality = own `make check` green). Not yet one report. |
| Tiered central runner | Implicit: CI runs 4 bootstrap cases, weekly runs the full matrix, each eval is its own script with its own flags. |
| Codified adversarial suite | Partially: the trust properties found by adversarial review are pinned as unit/integration tests; the 20-run cold-start evaluation itself was manual. |
| Regression baselines | None. Nothing stops generated output from silently bloating (or losing files) between releases — and token weight is a core promise. |
| Scenario fixtures | Cases are typed tuples inline in each eval — fine at current scale. |
| Real-workload studies | The 20-run cold-start evaluation (documented in CHANGELOG/PR #68) is exactly this, but it is methodology-by-anecdote, not a committed artifact. |
| Reproduce command with numbers | `docs/evals.md` does this. |

## Adopted in this branch

1. **Scaffold weight regression baselines** (headroom practices 1 + 4).
   `scripts/token_savings_eval.py` gains `--check-baselines` /
   `--update-baselines` against a committed
   `tests/fixtures/scaffold-weight-baselines.json` (per-case file count
   exact, content bytes within ±10%). This is the regression benchmark for
   kickstart's efficiency promise: template changes that bloat generated
   output or drop files now fail an eval instead of shipping silently.
   Deterministic by construction — no flaky timing, no model in the loop.
2. **Unified tiered eval runner** (practice 2).
   `scripts/run_evals.py --tier {smoke,pr,full}`: one entrypoint that
   orchestrates the existing evals and prints a single summary table.
   `smoke` = headline bootstrap case; `pr` = the four CI bootstrap cases +
   weight baselines; `full` = whole bootstrap matrix + token eval with
   baselines + determinism and website-examples test suites.

## Considered and deferred (with reasons)

- **Codifying the cold-start agent evaluation as a benchmark.** Headroom's
  agent benchmarks have an LLM in the loop; ours would too. That makes the
  numbers non-deterministic and expensive — useful as a release-time study
  (as run for v0.4.2), wrong as a committed pass/fail gate. Keep it a
  documented methodology, re-run per release line.
- **Latency benchmarks.** Generation is ~1s and `make check` seconds are
  already reported per bootstrap case; budgets on shared-runner wall time
  would mostly measure runner noise.
- **Separate `benchmarks/` tree.** Headroom splits benchmarks from tests;
  kickstart's evals already live in `scripts/` with unit tests in
  `tests/unit/scripts/`. One home is enough at this scale.
- **Worst-case suite.** The scaffold matrix eval (500 projects) already
  plays this role for generation; the adversarial CLI cases are pinned as
  tests.

## Follow-up candidates (not in this branch)

- Fold the paired headline into one published table: per scaffold, tokens
  saved *and* its own-check status from the same run.
- A committed scenario file for the cold-start evaluation prompts, so the
  per-release study stays comparable across releases.
