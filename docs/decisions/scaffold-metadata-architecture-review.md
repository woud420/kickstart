# Scaffold Metadata Architecture Review

Checked: 2026-07-07

Scope: evaluate the proposal to evolve `.kickstart/scaffold.json` from scaffold
metadata into a generalized "capability contract" describing runtime
operations, effects, policies, adapters, approvals, and retry semantics.

> **Revision note.** This revision corrects v1's central field-selection test.
> v1 judged every manifest field by "does the shipped tool read this today?"
> and recommended stripping the descriptive middle tier (`execution`,
> `artifacts`, `provider`, `capabilities`). That test was wrong: those fields
> are the desired-state spec a reconciler must read to regenerate the managed
> envelope — the drift-detection feature this review names as the moat.
> Applying the corrected test shows the manifest is *incomplete*, not bloated.
> The rejection of the capability-contract runtime layer is unchanged.

## Bottom Line

The capability-contract proposal should be **narrowed and renamed, not
implemented as described.** Abandon the runtime-semantics layer (effects,
policies, authorization, retry/idempotency declarations, tool registries,
workflow). Keep — and rename — the narrow, already-shipping
`capabilities.service_extensions` field, because that is the one part backed by
real generated code. Nothing in the rest of this review softens that
conclusion; if anything, it hardens it (§6).

On the metadata itself, this review reverses its own v1. The question that
decides every field is not "does anything read this today?" but:

> **Can the managed envelope be regenerated purely from `scaffold.json`?**

The managed envelope is the bounded set of files kickstart owns and must keep
aligned with the current standard: the manifest itself, `AGENTS.md`, the
`docs/` skeleton, the CI workflow file(s), the Makefile's standard verbs, and
the directory layout conventions. Reconciliation — the write step `adopt`
explicitly defers (`src/generator/adoption.py:1-7`) — means regenerating that
envelope from the manifest and re-aligning the working tree with it. Under
that model, `execution`, `artifacts`, `provider`, and `extensions` are not
emitted-only documentation; they are the reconciler's input. Stripping them
(v1's recommendation) would have broken the moat feature before it was built.

Applied honestly, the regeneration test cuts both ways:

- It **fails today in three concrete places**: a Python service and a Go
  service produce *identical manifests* (service language is never recorded),
  worker language is likewise unrecorded, and the Python `--framework` choice
  (fastapi vs minimal) appears nowhere. The fix is three narrow fields, not a
  new abstraction.
- It **still removes** `docs` and `semantics` (constants that feed no
  regeneration decision) and **still rejects** every runtime-semantics field:
  no generated file varies on `retry_safe`, so the test excludes the entire
  capability-contract layer by construction.

---

## 1. The Consumer Question, Answered

v1 mapped consumption and found that the shipped tool reads exactly three keys,
presence-only (`schema_version`, `project`, `lifecycle` —
`src/generator/adoption.py:92`); internal eval scripts read the middle tier;
and `generated_by`, `knowledge_adapter`, `docs`, `semantics` have no reader
anywhere. Those facts stand. What v1 got wrong was the inference. A manifest
field is not justified by having a reader *today*; it is justified by the
reader the design intends. This review left "who consumes this, and what
decision do they make with it?" open. Closing it:

**The consumer is the reconciler.** Its algorithm:

1. Read `scaffold.json` → know the project's kind, language, runtime,
   extensions, and artifact choices.
2. Re-derive the managed envelope the *current* kickstart standard would
   generate for that spec.
3. Three-way merge co-owned files (base: the template as of the version
   recorded in `generated_by`; theirs: the current template; ours: the working
   tree).
4. Apply non-conflicting updates; surface conflicts to the human. Never touch
   anything outside the envelope.

This is the Terraform posture, correctly scoped. Terraform does not reconcile
an entire cloud account; it reconciles only the resources it declares and
ignores everything else. Its plan/apply loop exists precisely *because* drift
is normal within that managed set — drift is the expected condition the tool
is built around, not an anomaly. Kickstart's analog: product code, domain
logic, and user-added files sit outside the envelope the way undeclared
resources sit outside Terraform state. "The user is supposed to build on top
of the scaffold" stops being an objection to drift detection the moment the
reconciler's scope is the envelope, not the repo.

Two facts about the current codebase keep this honest:

- **Reconciliation is entirely greenfield.** `kickstart upgrade` self-updates
  the installed binary (`src/utils/updater.py:1-8`); it never touches a
  scaffolded repo. `adopt` rejects anything but `--check`
  (`src/cli/main.py:96-98`). Nothing diffs generated content against current
  templates anywhere in `src/`.
- **No generated file carries ownership markers today.** No Makefile or CI
  template has any owned-vs-free boundary convention — no fences, no
  "managed by" comments (verified across `src/templates/`). The one existing
  precedent is internal: the installer maintains a `MARKER_BEGIN`/`MARKER_END`
  managed block inside user-owned shell rc files, refreshing only its block
  and preserving surrounding content (`src/utils/installer.py:263-303`). The
  mechanism exists in-repo; it has never been applied to templates.

---

## 2. Critique Of The Current Metadata Model

### 2.1 The real defect is incompleteness, not bloat

Testing "can the envelope be regenerated purely from the manifest?" against the
six `ScaffoldContract` construction sites:

| Input that shapes the envelope | Recorded in manifest? | Evidence |
|---|---|---|
| Service language (python/rust/ts/go/cpp) | **No — gap** | `service.py:172-181` sets no language; templates select `{language}/Makefile.tpl`, `ci-{language}.yml.tpl` (`stack/templates.py:12-40,157-170`) |
| Worker language (rust/ts) | **No — gap** | `service.py:236-243`; Rust emits `Cargo.toml`, TS emits `package.json` (`stack/templates.py:173-200`); only a fragile lifecycle proxy distinguishes them |
| Python service framework (fastapi/minimal) | **No — gap** | `service.py:410`; different `src/` tree and requirements (`template_plans.py:66-92`) |
| `--helm` for services | Yes | `runtime_platforms` + `artifacts.kubernetes` (`service.py:175-178`) |
| helm vs kustomize for systems | Yes | `artifacts.kubernetes` (`monorepo.py:170`, `registry.py:208-209`) |
| Library/CLI language | Yes | `artifacts.package` (`lib.py:141,218`) plus CLI profile fields |
| Frontend stack | Yes (implied) | fixed React/TS by kind (`frontend.py:17`) |
| Knowledge adapter, workspace tooling (system) | Yes | `monorepo.py:93-94` |

A Python service and a Go service — different Makefiles, Dockerfiles, CI
workflows, source layouts — serialize to *byte-identical manifests*. Whatever
one thinks of the manifest's size, a desired-state spec that cannot
distinguish those two repos cannot drive reconciliation. The manifest's
problem is the opposite of the one v1 diagnosed.

### 2.2 Criticisms from v1 that stand

- **`capabilities` is misnamed.** It holds exactly one thing —
  `service_extensions` (database/cache/auth), generation-time options backed
  by real code and a validated support matrix
  (`src/generator/service_capabilities.py:34-47`). The word "capabilities" is
  a pre-installed on-ramp to the runtime-contract scope creep this review
  rejects. Rename it for what it is: `extensions`.
- **The `worker` kind is a live inconsistency.** `project_kind: "worker"` is
  emitted for `kickstart service --runtime cloudflare-workers`
  (`service.py:236-243`), yet `worker` is not an exposed project type
  (`src/cli/dispatch.py:14-15`), README calls workers a generated thing, and
  AGENTS.md calls cloudflare-workers a service *runtime*. One concept, three
  stories. Workers should be `kind: "service"` with execution model
  `cloudflare-worker`; the `worker` branches in `_lifecycle()` and
  `contract_subjects` key off the runtime profile instead.
- **Two fields are genuinely inert under any test.** `docs` is five hardcoded
  paths identical in every manifest — the paths are fixed by convention, so
  regeneration never consults the field. `semantics` is a pure function of
  `schema_version` (`scaffold_contract.py:18`); serializing it per repo adds
  nothing the version doesn't already say.

### 2.3 A v1 criticism this revision withdraws

v1 flagged `execution.models`/`execution.platforms` as redundant (they co-vary
for every single-project kind) and proposed collapsing them. Under the
reconciler model the pair is load-bearing where it matters — `system` repos
carry genuinely independent multi-valued sets, and services split platform
from model on `--helm` — and harmless where it co-varies. Collapsing fields to
save bytes in a spec whose only reader is a machine is tidiness, not design.
Withdrawn.

Likewise `generated_by` and `knowledge_adapter` are rehabilitated, not
stripped:

- `generated_by` today emits the constant `"kickstart"` — useless. But the
  reconciler's three-way merge needs the *base version*: which release's
  templates originally produced this repo. Emit `kickstart@<version>` and the
  field becomes the merge base selector, the single most load-bearing datum in
  the file.
- `knowledge_adapter` selects generated files (Backstage `template.yaml`,
  `.obsidian/` config — `stack/templates.py:99-112`). It passes the
  regeneration test on its own merits. v1's suggestion to exile it to an
  exporter concern is withdrawn; fields that choose which files exist in the
  envelope belong in the spec.

---

## 3. Concepts To Remove, Add, Or Rename

**Remove:**

- `docs` — constant paths, fixed by convention, feed no regeneration decision.
- `semantics` — derivable from `schema_version`; keep the prose
  `scaffold-contract.md`, stop emitting the URL per repo.

**Add (the three gaps, as narrow fields — not abstractions):**

- `project.language` — required for every kind; today only libs/CLIs record it
  (indirectly, via `artifacts.package`).
- `project.framework` — optional; records fastapi/minimal and any future
  framework variant that changes generated output.
- (No third new field: worker language is covered by `project.language` once
  it exists.)

**Rename / restructure:**

- `capabilities` → `extensions`. Same content, honest name, closes the
  semantic door.
- `project_kind: "worker"` → retired. Workers become `kind: "service"` +
  `execution.models: ["cloudflare-worker"]`. Reconcile README/AGENTS/manifest
  to the runtime-profile story.
- `generated_by` → keep the key, change the value: `kickstart@<version>`.

**Keep as-is (now with a named consumer):**

- `schema_version`, `project`, `lifecycle` — consumed by `adopt` today.
- `execution`, `artifacts`, `provider`, `extensions`, `knowledge_adapter`,
  `composition` (system) — the reconciler's desired-state spec.

---

## 4. Architectural Boundary: What Kickstart Owns

**Kickstart owns the managed envelope of a repository and its conformance to
the current standard.** It is Terraform for repository structure: a bounded
declared scope, reconciled; everything outside it, untouched.

| Kickstart OWNS | Kickstart does NOT own |
|---|---|
| The managed envelope: manifest, `AGENTS.md`, `docs/` skeleton, CI workflow, Makefile standard verbs, layout conventions | Product/domain code and any user-added file |
| Regenerating that envelope from `scaffold.json` | Runtime behavior / execution |
| Lifecycle **verbs** (`make check`, etc.) | What those verbs *do* at runtime |
| Generation-time extensions that produced code | API contracts (→ OpenAPI/AsyncAPI) |
| Conformance: adopt, drift, audit, repair, upgrade | Effect systems / idempotency / retry semantics |
| **Exports** to existing ecosystems | Authorization / policy (→ OPA); workflow (→ Temporal); tool registries (→ MCP) |

The regeneration test polices this boundary mechanically, and its scope must
be stated to close a loophole: **a field earns its place only by determining
which generated file exists or what its generated content is.** "Needed for
regeneration" can never justify `retry_safe`, `idempotent`,
`requires_approval`, effects, or policy — no template varies on them, so they
fail the test by construction. If a future template *were* made to vary on
such a field, that template would be generating runtime behavior, which the
mission statement already forbids; the field and the template fail together.
The test is not a backdoor.

One scope caution on the reconciler itself: conflict resolution must stay
**structural, not semantic**. The three-way merge compares text/structure of
generated files; it never interprets what a user's Makefile target or CI job
*does*, and it resolves nothing by policy — conflicts go to the human. A
reconciler that "decides whose change wins" by reasoning about behavior would
be the capability-contract mistake re-entering through the back door.

---

## 5. Target Metadata Model

Every field either is consumed by `adopt` today or feeds envelope
regeneration. Illustrative service manifest (schema 4.0):

```json
{
  "schema_version": "4.0",
  "generated_by": "kickstart@0.4.3",
  "project": {
    "name": "my-api",
    "kind": "service",
    "language": "python",
    "framework": "fastapi",
    "repo_layout": "single-project"
  },
  "execution": {
    "models": ["container"],
    "platforms": ["kubernetes"]
  },
  "artifacts": {
    "image": "dockerfile",
    "kubernetes": "helm",
    "ci": "github-actions"
  },
  "provider": {
    "targets": []
  },
  "extensions": {
    "database": "postgres",
    "cache": "redis",
    "auth": "jwt"
  },
  "lifecycle": {
    "install": "make install",
    "test": "make test",
    "check": "make check",
    "build": "make build",
    "dev": "make dev"
  }
}
```

Changes from 3.0: add `project.language` and `project.framework` (the
regeneration gaps); `generated_by` carries the version; `capabilities` →
`extensions`; `docs` and `semantics` dropped; `worker` retired as a kind
(a Cloudflare Worker is `kind: "service"`, `execution.models:
["cloudflare-worker"]`, `artifacts.worker: "wrangler"`, `provider.targets:
["cloudflare"]`). Systems keep `composition` and `knowledge_adapter`; both
select generated files, so both pass the test.

Ship a **JSON Schema** generated from the TypedDicts as the structural source
of truth; `scaffold-contract.md` remains commentary, not authority. Schema
migration 3.0 → 4.0 needs a documented, tested upgrade path — which is itself
the first small exercise of the reconciler (the manifest is the first co-owned
file it learns to rewrite).

---

## 6. Roadmap

### Strengthen (the moat — sequenced, with an explicit go/no-go)

The reconciler is the feature; everything here exists to de-risk it. Today
`adopt --check` verifies presence of nine artifacts, three manifest keys, and
a Makefile `check` target (`src/generator/adoption.py`). From there:

1. **Complete the spec.** Add `project.language` / `project.framework`,
   version `generated_by`. Without this, step 3 cannot even select templates.
2. **Drift report (read-only).** `adopt --check` grows a mode that regenerates
   the envelope from the manifest into a temp tree and reports file-level
   divergence by class: scaffold drift, docs drift, CI drift, artifact drift.
   Read-only, so it is safe to ship early and it measures the real-world
   signal-to-noise of drift detection before any write path exists.
3. **Three-way merge prototype — one file type only.** Makefile standard
   targets first: base = template at `generated_by`'s version, theirs =
   current template, ours = working tree. The `installer.py` managed-block
   mechanism (`src/utils/installer.py:263-303`) is the in-repo precedent for
   maintaining an owned region inside a user-edited file; new templates can
   adopt explicit markers so future repos merge trivially, while pre-marker
   repos rely on the structural merge.
4. **Go/no-go.** Only if the prototype shows acceptable conflict rates does
   `repair`/`upgrade` become a flagship commitment. This is greenfield work —
   no reconciliation code exists today and no template carries ownership
   markers — and the roadmap should not pretend otherwise. If the prototype
   drowns in conflicts, the fallback posture is still valuable: read-only
   drift reporting plus regenerate-into-a-branch, letting git and the human do
   the merge.

### Simplify

- Drop `docs` and `semantics`; version `generated_by`.
- Rename `capabilities` → `extensions`.
- Retire the `worker` kind; reconcile README/AGENTS/manifest on the
  runtime-profile story.
- Publish the JSON Schema.

### Remove (keep out of scope — unchanged from v1)

- Capability DSL, generalized effect systems, runtime semantic contracts.
- Policy/authorization engines, workflow/orchestration engines.
- Retry/idempotency/approval declarations.
- Tool/operation registries as first-class manifest concepts.

### Postpone

- **Exporters** (OpenAPI, MCP annotations, Backstage `catalog-info.yaml`,
  AsyncAPI). On-mission as derived projections, but they come after the spec
  is complete and drift reporting exists. The `backstage-catalog` skill is the
  model: derive from `scaffold.json` plus generated code; never invent
  intermediate metadata. Exporters write *out* to ecosystems; they do not pull
  ecosystem concepts *in*.
- Provider-specific runtime detail stays attached to deployment artifacts
  (Terraform/Wrangler files), not repository metadata.

---

## 7. Recommendation On Capability Contracts

**Narrow + rename. Do not implement the proposed runtime-semantics layer.**

- **Abandon:** effects, policies, authorization, retry/idempotency/approval
  semantics, tool registries, workflow, generalized capability DSL. These
  belong to OpenAPI/AsyncAPI, OPA, Temporal, and MCP; kickstart exports to
  them, full stop.
- **Narrow:** the only "capability" with real backing is
  `service_extensions` — code kickstart actually generates and validates.
  Keep that, renamed, and nothing more under this heading.
- **Rename:** `extensions`. The word "capability" is itself a scope-creep
  vector.

The reconciliation reframe *strengthens* this rejection. Under the
regeneration test, a manifest field must select generated files or content.
`retry_safe: true` selects nothing — kickstart generates no code whose shape
depends on it, and a declaration without a generator behind it is a claim the
repo cannot keep. The capability-contract layer is not just off-mission; under
the governing test it is unexpressible.

---

## Answers To The Specific Questions

1. **Is "capability" the right abstraction?** No. The only real instance is
   generated extensions; keep metadata scaffold-oriented and rename the field.
2. **Would "operations" be better than "capabilities"?** No — "operations"
   implies runtime-invocable units (MCP/OpenAPI territory) and invites the
   same creep. Use `extensions`.
3. **Which fields are consumed today?** By the shipped tool: `schema_version`,
   `project`, `lifecycle` (presence-only, `adoption.py:92`). By internal
   evals: `execution`, `artifacts`, `provider`, `capabilities`,
   `composition`. By the Backstage skill: `project`, `execution.models`,
   `capabilities`, `docs`. Going forward the reconciler consumes the entire
   spec — that is the design intent the fields were waiting on.
4. **Which exist only for documentation?** After this revision, two:
   `docs` and `semantics` — and they should be dropped. v1's longer list
   (`generated_by`, `knowledge_adapter`) was wrong: both feed regeneration.
5. **Can existing metadata be simplified?** Marginally (drop two constants,
   one rename) — but the accurate statement is that it must be *completed*:
   `project.language` and `project.framework` are missing, and without them
   the manifest cannot distinguish a Python service from a Go one.
6. **Should knowledge adapters be a plugin/export mechanism?** The *adapter
   outputs* (Backstage/Obsidian files) are export-shaped, but the field stays
   in the manifest: it selects generated files, so the reconciler needs it.
7. **Should provider-specific concepts move toward deployment artifacts?**
   Yes for runtime detail; `provider.targets` stays only as the coarse
   selector of which IaC templates the envelope contains.
8. **Is the semantics reference document still justified?** The prose doc yes,
   as commentary; the per-repo `semantics` URL field no. The JSON Schema
   becomes the structural authority.
9. **Should project kinds be simplified — is "worker" a kind?** Not a kind: an
   execution profile of `service`. Retire it and reconcile the docs.
10. **Is the long-term moat conformance rather than generation?** Yes, with an
    honest caveat: the moat is *earned* by solving co-owned-file
    reconciliation, which is greenfield and unproven here. Sequence it
    (complete spec → read-only drift report → single-file merge prototype →
    go/no-go) rather than declaring it. Generation remains the on-ramp and the
    thing that makes the manifest trustworthy in the first place.

---

## Guiding Principle Applied

Every kept field answers "does this improve deterministic repository
scaffolding without making kickstart responsible for application behavior?"
with yes, and now for a checkable reason: each one selects generated files or
their content, so the envelope can be regenerated from the manifest alone.
Every rejected field fails the same test — the runtime-semantics layer
describes behavior no template generates, and the two dropped constants
select nothing at all. The boundary is no longer a matter of taste; it is the
regeneration test, applied without exception.
