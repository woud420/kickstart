# Architecture Evidence Pilot

Checked: 2026-09-01

## Bottom Line

Do not adopt [PR #104](https://github.com/woud420/kickstart/pull/104)'s
repository-local `.github` implementation. Keep architecture-evidence analysis
report-only and portable through the
[`analyze-graph-evolution` skill](https://github.com/woud420/skills/pull/12).
Do not add a GitHub Action, PR commentary, merge gate, or production refactor
from this pilot.

The portable-skill work is tracked by
[ENG-343](https://linear.app/polarcoordinates/issue/ENG-343/promote-architecture-evidence-analysis-into-the-portable-skillpack).
A possible reusable Action is a separate, evidence-gated decision tracked by
[ENG-344](https://linear.app/polarcoordinates/issue/ENG-344/qualify-a-reusable-architecture-evidence-action-after-multi-repository).

## What Was Tried

- An isolated report-only implementation at commits `90ae911` and `d382262`.
- Deterministic Code Review Graph snapshots and comparisons, a bounded
  behavioral oracle, a 100-case historical study, Delphi-inspired review,
  adjudication, a report, and a static evidence SPA.
- Nine `.github` files and 4,251 lines, including a 76-dependency exact lock;
  no production source changes.
- A supply-chain-hardened direct runner because the official composite Action
  did not transitively pin its package or nested Actions.

The three evidence lanes were evaluated separately. No composite quality score
was produced.

## Machine Evidence

- The analyzer was CRG 2.3.8. Its wheel SHA-256 was
  `013ae3c119cc7de337f9e88fe36daef82e2d4def942a014edcf97f126e208547`.
- Direct parser coverage was 163 of 385 source-like files (42.3%) and 76.1% by
  bytes. All 222 `.tpl` files were unsupported, materially limiting evidence
  in this template-centric repository.
- The final comparison was `not_comparable`, with reason
  `not comparable; rebaseline required`, because configuration changed. No
  topology delta is admissible from that comparison.
- Topology and CRG risk remain observations. They are not Kickstart's
  architecture authority or proof of quality.

## Behavioral Evidence

- Declared intent: `preserve`; result: `supported`.
- Eight bounded old-domain cases matched with zero unexpected differences and
  no public compatibility changes.
- This supports that the sampled observable behavior was preserved while the
  pilot infrastructure ran. It does not establish universal equivalence or
  make graph signals useful.
- Across the historical cases, behavior was labelled 17 measured, 67 inferred,
  and 16 unavailable. Every historical result remained inconclusive.

## Delphi-Inspired Judgment

- The method was a **Delphi-inspired correlated agent panel**, not independent
  expert confidence. The facilitator did not vote.
- Round 1 was blind to graph evidence: 36 converged, 60 divergent, and 4
  insufficient, with 10 abstentions.
- After graph disclosure, Round 2 was 68 converged, 28 divergent, and 4
  insufficient, with 167 rating revisions. Round 3 produced no further rating
  changes.
- Agreement can prioritize investigation only. It cannot prove behavior,
  authorize a merge, or override contradictory or inconclusive evidence.

## Chronological Holdout

The frozen pilot design used 100 primary cases: 50 signal-enriched and 50
matched controls, split into 70 discovery and 30 newer holdout cases with seed
`6149`.

- Signal-enriched holdout hit rate: 0 of 14.
- Matched-control holdout hit rate: 1 of 14.
- Precision among the top five machine-ranked cases: 0%.
- Seven confirmed false positives, four false negatives, four explicitly
  adjudicated anchoring cases, and two unresolved holdout cases.
- Graph evidence found zero useful concerns missed by the blind panel and
  missed four concerns itself.
- One credible non-obvious holdout story survived: extraction of CI-only
  Cloudflare Worker smoke behavior that import topology could not see.
- Repeated-run determinism passed, but operational time and context savings
  were not measured.

The current portable skill has since tightened its schema and sampling
contract. The legacy 100-case bundle cannot certify the current runner; any new
historical claim requires a current-schema rebaseline.

## Decision

Close PR #104 rather than merge it. The held-out signal underperformed matched
controls, graph disclosure produced anchoring without demonstrated accuracy
gain, parser coverage omitted core template surfaces, and the final topology
comparison was not comparable. Behavior preservation was supported, but
usefulness was not. Supply-chain hardening made the prototype safer; it did not
make its signal actionable or justify its repository-local maintenance cost.

Generic metric, behavioral-evidence, Delphi, evaluation, rendering, and
verification machinery belongs in the portable skillpack. Kickstart owns this
repository-specific decision, its behavioral oracle and boundaries, and any
future thin opt-in integration.

## Criteria to Reconsider a GitHub Action

ENG-344 may recommend an experimental Action only after a preregistered,
current-schema study demonstrates all of the following:

- matching analyzer, configuration, corpus, evaluator, normalizer, policy, and
  environment digests;
- acceptable coverage of each selected repository's source-of-truth surfaces;
- signal-enriched chronological holdouts outperform matched controls with
  non-zero frozen top-k precision;
- useful adjudicated concerns exceed misses, with anchoring limits declared
  before outcome reveal;
- approximately 30–50 real pull requests across multiple repositories have
  been observed;
- measured operational value justifies the maintenance and supply-chain cost;
- the runner is immutable, secretless, hostile-artifact validated, and remains
  report-only.

PR commentary, merge gates, and refactor authorization each require separate
evidence and approval. A graph score can never compensate for contradicted or
inconclusive behavioral evidence.

## Non-Goals

- No composite quality score or confidence interval from correlated agents.
- No claim that CRG is an architecture authority.
- No automatic refactor or production-source change.
- No authorization for the proposed `src/cli/main.py` adapter extraction.
- No treatment of a later SCC reduction as proof of a fix.
- No repository-hosted SPA, raw graph database, or source archive.
- No claim of universal behavioral equivalence from a bounded oracle.
