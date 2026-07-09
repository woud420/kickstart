# Scaffold Metadata Architecture Review

Checked: 2026-07-07

Scope: evaluate the proposal to evolve `.kickstart/scaffold.json` from scaffold
metadata into a generalized "capability contract" describing runtime
operations, effects, policies, adapters, approvals, and retry semantics.

> **Revision note.** v1 judged every manifest field by "does the shipped tool
> read this today?" and recommended stripping the descriptive middle tier
> (`execution`, `artifacts`, `provider`, `capabilities`). That test was wrong:
> those fields are the desired-state spec a reconciler must read to regenerate
> what kickstart owns — the drift-detection feature this review names as the
> moat. This revision also incorporates an adversarial review pass that
> corrected the earlier draft's overclaims about how mechanical that test is
> and how feasible the reconciler is today. The rejection of the
> capability-contract runtime layer is unchanged throughout.

## Vocabulary

Four terms carry this review; each is bounded here and used in no other sense.

- **Generated set** — every file kickstart emits at scaffold time, from
  `AGENTS.md` down to starter source files.
- **Managed envelope** — the subset of the generated set kickstart keeps
  aligned with the current standard over time: `.kickstart/scaffold.json`
  itself, `AGENTS.md`, the `docs/` skeleton (architecture/contracts/
  operations/decisions), the CI workflow file(s), the Makefile's standard
  targets, and the directory layout conventions.
- **Seeds** — the rest of the generated set: starter source code, extension
  wiring (database clients, auth handlers), migrations, example tests, README
  prose. Generated once, owned by the user from the first commit, never
  re-aligned.
- **Co-owned file** — a file that mixes envelope content with user content
  (the Makefile carries kickstart's standard targets and the user's own; a CI
  workflow carries the standard check job and the user's added jobs).

## Bottom Line

The capability-contract proposal should be **narrowed and renamed, not
implemented as described.** Abandon the runtime-semantics layer (effects,
policies, authorization, retry/idempotency declarations, tool registries,
workflow). Keep — and rename — the narrow, already-shipping
`capabilities.service_extensions` field, because that is the one part backed by
real generated code. Nothing in the rest of this review softens that
conclusion (§7).

On the metadata itself, this review reverses its own v1. The question that
decides every field is not "does anything read this today?" but:

> **Can the generated set be re-derived purely from `scaffold.json`?**

Reconciliation — the write step `adopt` explicitly defers
(`src/generator/adoption.py:1-7`) — means re-deriving what the current
standard would generate for this project and re-aligning the *managed
envelope* against it, leaving seeds and user files untouched. Under that
model, `execution`, `artifacts`, `provider`, and the extensions field are not
emitted-only documentation; they are the reconciler's input. Stripping them
(v1's recommendation) would have broken the moat feature before it was built.

Two honest limits on that test, both surfaced by adversarial review:

- **It is necessary, not sufficient.** The test admits any field a template
  varies on — including, in principle, a smuggled runtime-semantics field
  shipped with a new template. A second, explicitly non-mechanical gate does
  the excluding: the mission boundary (§4).
- **It fails today in three concrete places**: a Python service and a Go
  service produce *identical manifests* (service language is never recorded),
  worker language is likewise unrecorded, and the Python `--framework` choice
  (fastapi vs minimal) appears nowhere. An exhaustive sweep of every other
  generation input (`--cloud`, system runtime profiles, workspace tooling,
  `--helm`, `gh`/`root`/config — the last three never feed template content)
  found no fourth gap. The fix is narrow fields, not a new abstraction —
  though fields alone are not the whole fix (§6 step 1).

The test still removes `docs` and `semantics` (constants that feed no
regeneration decision — with one sequencing caution on `semantics`, §3), and
the two gates together still exclude every runtime-semantics field.

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

**The consumer is the reconciler.** Its intended algorithm:

1. Read `scaffold.json` → know the project's kind, language, runtime,
   extensions, and artifact choices.
2. Re-derive the managed envelope the *current* kickstart standard would
   generate for that spec.
3. For co-owned files, reconcile using the version recorded in `generated_by`
   as the base reference (§6 details what this actually requires — the
   version string alone is not enough).
4. Apply updates only inside kickstart-owned regions; surface everything else
   to the human. Never touch seeds or user files.

This is the Terraform posture at the repository boundary: Terraform does not
reconcile an entire cloud account; it reconciles only the resources it
declares and ignores everything else. Its plan/apply loop exists precisely
*because* drift is normal within that managed set. Kickstart's analog: seeds
and user files sit outside the envelope the way undeclared resources sit
outside Terraform state, and "the user is supposed to build on top of the
scaffold" stops being an objection to drift detection once the reconciler's
scope is the envelope, not the repo.

The analogy must be qualified where it breaks: a Terraform-managed resource is
*wholly* owned — users are not expected to hand-edit it. Kickstart's envelope
includes co-owned files, where owned and user content interleave line-by-line
within a single file. Terraform never reconciles a half-declared object; the
reconciler must, on every Makefile and CI workflow. That intra-file boundary —
not the repo-vs-envelope boundary — is the unproven part of the whole design,
and §6 sequences the roadmap around proving or abandoning it.

Three facts about the current codebase keep this honest:

- **Reconciliation is entirely greenfield.** `kickstart upgrade` self-updates
  the installed binary (`src/utils/updater.py:1-8`); it never touches a
  scaffolded repo. `adopt` rejects anything but `--check`
  (`src/cli/main.py:96-98`). Nothing diffs generated content against current
  templates anywhere in `src/`.
- **No envelope-membership record exists.** Envelope files and seeds are
  written through the identical generation path
  (`src/generator/base.py:381-478`) with no tag or manifest entry
  distinguishing them. "Re-derive the envelope" today would re-derive the
  entire generated set with nothing marking which regenerated files the
  reconciler may act on. A persisted per-file ownership classification
  (envelope vs seed) is prerequisite work, not a byproduct of adding fields.
- **No generated file carries ownership markers.** No Makefile or CI template
  has any owned-vs-free boundary convention (verified across
  `src/templates/`). The one in-repo precedent is the installer's
  `MARKER_BEGIN`/`MARKER_END` block in shell rc files
  (`src/utils/installer.py:263-303`) — and it is *whole-block replacement*,
  not a merge: it substitutes the fenced region wholesale and would discard a
  user's edit inside it. It demonstrates region boundaries, nothing more.

---

## 2. Critique Of The Current Metadata Model

### 2.1 The real defect is incompleteness, not bloat

Testing "can the generated set be re-derived purely from the manifest?"
against the six `ScaffoldContract` construction sites:

| Input that shapes generated output | Recorded in manifest? | Evidence |
|---|---|---|
| Service language (python/rust/ts/go/cpp) | **No — gap** | `service.py:172-181` sets no language; templates select `{language}/Makefile.tpl`, `ci-{language}.yml.tpl` (`stack/templates.py:12-40,157-170`) |
| Worker language (rust/ts) | **No — gap** | `service.py:236-243`; Rust emits `Cargo.toml`, TS emits `package.json` (`stack/templates.py:173-200`); only a fragile lifecycle proxy distinguishes them |
| Python service framework (fastapi/minimal) | **No — gap** | `service.py:410`; different `src/` tree and requirements (`template_plans.py:66-92`) |
| `--helm` for services | Yes | `runtime_platforms` + `artifacts.kubernetes` (`service.py:175-178`) |
| helm vs kustomize for systems | Yes | `artifacts.kubernetes` (`monorepo.py:170`, `registry.py:208-209`) |
| System `--cloud` (aws/gcp/cloudflare/multi/none) | Yes | `provider.targets` (`monorepo.py:92`) |
| Library/CLI language | Yes | `artifacts.package` (`lib.py:141,218`) plus CLI profile fields |
| Frontend stack | Yes (implied) | fixed React/TS by kind (`frontend.py:17`) |
| Knowledge adapter, workspace tooling (system) | Yes | `monorepo.py:93-94` |

A Python service and a Go service — different Makefiles, Dockerfiles, CI
workflows, source layouts — serialize to *byte-identical manifests*. Whatever
one thinks of the manifest's size, a desired-state spec that cannot
distinguish those two repos cannot drive reconciliation. The manifest's
problem is the opposite of the one v1 diagnosed.

### 2.2 Criticisms from v1 that stand

- **The current `capabilities` field is misnamed.** It holds exactly one
  thing — `service_extensions` (database/cache/auth), generation-time options
  backed by real code and a validated support matrix
  (`src/generator/service_capabilities.py:34-47`). The word "capabilities" is
  a pre-installed on-ramp to the runtime-contract scope creep this review
  rejects. Rename it for what it is: `extensions` (§3 specifies the shape).
- **The `worker` kind is a live inconsistency.** `project_kind: "worker"` is
  emitted for `kickstart service --runtime cloudflare-workers`
  (`service.py:236-243`), yet `worker` is not an exposed project type
  (`src/cli/dispatch.py:14-15`), README calls workers a generated thing, and
  AGENTS.md calls cloudflare-workers a service *runtime*. One concept, three
  stories. Workers should be `kind: "service"` with execution model
  `cloudflare-worker`; the `worker` branches in `_lifecycle()` and
  `contract_subjects` key off the runtime profile instead.
- **Two fields are genuinely inert.** `docs` is five hardcoded paths identical
  in every manifest — the paths are fixed by convention, so regeneration never
  consults the field, and nothing reads it (the Backstage skill keys techdocs
  on the presence of the `docs/` *directory*, not the manifest field).
  `semantics` is a constant URL per release. Both go — but see §3 for a
  sequencing constraint the earlier draft missed.

### 2.3 A v1 criticism this revision withdraws, and what that admits

v1 flagged `execution.models`/`execution.platforms` as redundant (they co-vary
for every single-project kind) and proposed collapsing them. This revision
keeps the pair: `system` repos carry genuinely independent multi-valued sets,
services split platform from model on `--helm`, and collapsing fields to save
bytes in a machine-read spec is tidiness, not design.

Keeping them is, however, a judgment call the field-selection test does not
make. The same is true of the CLI profile fields (`cli_framework`,
`command_root`, `entrypoint`, `operation_root`, `src_root_files`,
`architecture`): once `project.language` exists, all of them are pure
functions of language and kind (`lib.py:235-265`), so strict necessity would
drop them. They stay because they serve a different, existing reader — agents
orienting in a generated repo read them directly rather than re-deriving
kickstart's language conventions. The rule, stated honestly: **necessity
mandates a field's presence; redundancy is permitted where a named reader
benefits.** The test yields a floor, not a unique field set.

Two rehabilitations, with corrections from adversarial review:

- `generated_by` today emits the constant `"kickstart"`. Emit
  `kickstart@<version>` and it records which release produced the repo — the
  base reference any reconciliation needs. (The earlier draft called this "the
  single most load-bearing datum"; that presumed the three-way merge design
  ships. If the fallback posture wins instead — §6 step 4 — git supplies the
  base and this field matters far less. It is load-bearing *if* the merge path
  is taken.)
- `knowledge_adapter` selects generated files (Backstage `template.yaml`,
  `.obsidian/` config — `stack/templates.py:99-112`) and passes the test on
  its own merits. v1's suggestion to exile it to an exporter concern is
  withdrawn.

---

## 3. Concepts To Remove, Add, Or Rename

**Remove (with one ordering constraint):**

- `docs` — constant paths, fixed by convention, feed no regeneration decision,
  no reader anywhere.
- `semantics` — a constant URL per release. Correction from review: it is a
  function of the generating *tool version* (`__version__`), not of
  `schema_version` (`scaffold_contract.py:18` embeds `v{__version__}`), which
  means it is currently the **only place the generating version is recorded**.
  Version `generated_by` first; drop `semantics` after. Dropping it first
  would destroy the one datum the reconciler needs from existing repos.

**Add (the three gaps, as narrow fields — not abstractions):**

- `project.language` — required for every kind; today only libs/CLIs record it
  (indirectly, via `artifacts.package`).
- `project.framework` — optional; records fastapi/minimal and any future
  framework variant that changes generated output.
- (No third new field: worker language is covered by `project.language` once
  it exists.)

**Rename / restructure:**

- `capabilities` → `extensions`, and the `service_extensions` nesting level is
  deliberately collapsed: `capabilities.service_extensions.{database,cache,auth}`
  becomes `extensions.{database,cache,auth}`. This is a structural change, not
  a pure rename — schema 4.0 breaks the old access path, and consumers (the
  Backstage skill reads `capabilities.service_extensions` today) migrate with
  the schema bump.
- `project_kind: "worker"` → retired. Workers become `kind: "service"` +
  `execution.models: ["cloudflare-worker"]`. Reconcile README/AGENTS/manifest
  to the runtime-profile story.
- `generated_by` → keep the key, change the value: `kickstart@<version>`.

**Keep as-is (now with a named reader):**

- `schema_version`, `project`, `lifecycle` — consumed by `adopt` today.
- `execution`, `artifacts`, `provider`, the renamed extensions field, and (for
  systems) `knowledge_adapter` and `composition` — the reconciler's
  desired-state spec, plus direct agent consumption.

A naming note the review surfaced: an `execution` block in a manifest whose
mission disowns "execution" is the same vocabulary hazard that motivated
renaming `capabilities`. Its content is legitimate — the values select which
packaging and deploy files exist (Dockerfile vs wrangler config), nothing
more. Renaming it (`packaging`, `runtime_target`) is defensible but breaks
more consumers than it protects; the cheaper guard is this explicit scope
statement, which `scaffold-contract.md` should carry: **`execution` records
which runtime-artifact files the scaffold generated, never how code behaves.**

---

## 4. Architectural Boundary: What Kickstart Owns

**Kickstart owns the managed envelope of a repository and its conformance to
the current standard.** Everything else it generates once — seeds — and then
treats as the user's.

| Kickstart OWNS | Kickstart does NOT own |
|---|---|
| The managed envelope (see Vocabulary) | Seeds after first commit; product/domain code; any user-added file |
| Re-deriving the generated set from `scaffold.json` | Runtime behavior / execution |
| Standard target *existence* and marker-fenced standard recipe bodies | Recipe content users have customized; what any target does at runtime |
| Generation-time extensions, as a closed allowlist | API contracts (→ OpenAPI/AsyncAPI) |
| Conformance: adopt, drift, audit, repair, upgrade | Effect systems / idempotency / retry semantics |
| **Exports** to existing ecosystems | Authorization / policy (→ OPA); workflow (→ Temporal); tool registries (→ MCP) |

### Two gates, stated honestly

The earlier draft claimed the regeneration test polices this boundary
"mechanically, without exception." Adversarial review broke that claim, and it
deserved to break: `extensions.auth: "jwt"` makes a template emit JWT
verification code — runtime behavior — and passes the test. A smuggled
`idempotent: true` shipped with an idempotency-middleware template would be
structurally indistinguishable. The test cannot draw the line by itself.

The boundary is therefore two gates:

1. **The regeneration test (mechanical).** A field earns manifest presence
   only by determining which generated file exists or what its generated
   content is. This is checkable and excludes free-floating declarations —
   `retry_safe: true` with no template behind it selects nothing and fails
   here.
2. **The mission gate (policy).** Among fields that pass gate 1, kickstart
   blesses a deliberately closed allowlist of generated behaviors: today,
   database/cache/auth wiring with a validated support matrix
   (`service_capabilities.py:34-47`), emitted as *seeds* — generated once,
   never reconciled, never enforced. Extending the allowlist (an
   idempotency-middleware extension, an approval-flow extension) is a
   deliberate scope decision to be argued against the mission statement, not
   something any test grants. This gate is a judgment; pretending otherwise
   was the earlier draft's error.

The distinction between an extension and a capability contract is exactly the
seed/envelope distinction: an extension generates starter code the user owns
from day one; a capability contract asserts an ongoing property of runtime
behavior that no scaffold can keep true. Kickstart may do the former, narrowly;
it must never do the latter.

One scope caution on the reconciler: for make and CI YAML, **a textually clean
merge is not behavior-preserving** — make resolves duplicate targets by last
definition, variable effects depend on ordering and `include`s, and a merged
workflow can silently change the job graph. The reconciler therefore never
auto-applies into co-owned files outside explicitly marker-fenced regions, and
it resolves nothing by judgment: whole fenced regions are kickstart's to
replace, everything else goes to the human (or to git, in the fallback
posture). A reconciler that reasoned about what a user's target *does* in
order to merge it would be the capability-contract mistake re-entering through
the back door.

---

## 5. Target Metadata Model

Every field either is consumed by `adopt` today, feeds re-derivation of the
generated set, or serves a named reader. Illustrative service manifest
(schema 4.0):

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
    "kubernetes": "helm"
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
`extensions` with the `service_extensions` level collapsed (declared breaking
change, §3); `docs` and `semantics` dropped (in that order — `semantics` only
after `generated_by` is versioned); `worker` retired as a kind (a Cloudflare
Worker is `kind: "service"`, `execution.models: ["cloudflare-worker"]`,
`artifacts.worker: "wrangler"`, `provider.targets: ["cloudflare"]`). Systems
additionally keep `composition` and `knowledge_adapter`; both select generated
files. (Services do not emit `artifacts.ci` today — the CI workflow is
derivable from kind + language — so the example omits it.)

Ship a **JSON Schema** generated from the TypedDicts as the structural source
of truth; `scaffold-contract.md` remains commentary, not authority. The
3.0 → 4.0 migration needs a documented, tested upgrade path — a deterministic,
tool-owned rewrite of a file users don't hand-edit. That makes it safe early
work, and deliberately *not* evidence about the co-owned merge problem, which
it resembles in neither difficulty nor risk.

---

## 6. Roadmap

### Strengthen (the moat — sequenced, with an explicit go/no-go)

The reconciler is the feature; everything here exists to de-risk it. Today
`adopt --check` verifies presence of nine artifacts, three manifest keys, and
a Makefile `check` target (`src/generator/adoption.py`). The honest scope of
the work, incorporating the feasibility review:

1. **Complete the spec — fields plus regeneration inputs.** Add
   `project.language`/`project.framework`, version `generated_by`. But fields
   alone do not make the manifest executable: generators take CLI-style
   arguments and inject render inputs the manifest never records — toolchain
   pins via `toolchain_vars()` (`base.py:146-152`), extension conditionals,
   post-write mutations like the requirements append (`service.py:445-456`).
   Re-derivation therefore needs (a) a manifest→generator-arguments driver,
   (b) persisted render inputs (or hashes of rendered envelope files) so a
   faithful base can be reconstructed, and (c) a persisted per-file ownership
   classification (envelope vs seed), which does not exist today. A version
   string alone cannot rebuild the base file.
2. **Drift report (read-only), scoped to what is decidable.** Regenerate the
   envelope from the manifest into a temp tree and report divergence by class
   (scaffold, docs, CI, artifact). For co-owned files in pre-marker repos,
   report only structural facts — standard target missing, standard job
   absent — not content diffs, which would misread legitimate user
   customization as drift. User-owned surfaces inside artifact files (Helm
   values, k8s configuration) are out of scope by definition. This step is
   also the instrument that *verifies* manifest sufficiency: the three gaps
   were found by inspection, and regenerate-and-diff is what proves no others
   remain.
3. **Ownership markers + a merge prototype on one file type.** New templates
   gain explicit owned-region markers (the installer's block mechanism
   demonstrates the boundary pattern — and also its limit: block replacement
   clobbers edits inside the region, so fenced regions must be ones users are
   told not to edit). Prototype reconciliation on a *structured* file first —
   the CI workflow, where YAML parses into nodes and kickstart's job is
   separable — before attempting Makefiles, which have no structure, no
   in-repo parser, and last-definition-wins semantics. Templates would also
   need to be retrievable per release (bundled sets or fetched by tag);
   today the binary ships only the current generation
   (`base.py:75`, `updater.py:1-8`).
4. **Go/no-go.** Only if the prototype shows acceptable conflict rates does
   `repair`/`upgrade` become a flagship commitment. This is greenfield work
   with named prerequisites, and the roadmap should not pretend otherwise. If
   the prototype drowns in conflicts, the fallback posture is still valuable:
   read-only drift reporting plus regenerate-into-a-branch, letting git and
   the human do the merge.

### Simplify

- Version `generated_by`; then drop `semantics`; drop `docs`.
- Rename `capabilities` → `extensions` (nesting collapsed, declared breaking).
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
- **Narrow:** the only "capability" with real backing is the extension set —
  code kickstart actually generates and validates, emitted as seeds. Keep
  that, renamed, and nothing more under this heading. The allowlist is closed;
  additions are mission decisions, not schema decisions.
- **Rename:** `extensions`. The word "capability" is itself a scope-creep
  vector.

The reconciliation reframe sharpens *why*: a manifest field must select
generated files or content (gate 1), and kickstart only generates behaviors on
a closed, deliberately narrow allowlist (gate 2). A `retry_safe: true` with no
generator behind it fails gate 1 — it is a claim the repo cannot keep. The
same declaration *with* a generator behind it fails gate 2 — expanding the
blessed behavior set toward runtime semantics is exactly the mission creep the
original brief warned against. Neither gate alone rejects the proposal; the
two together, with the seed/envelope distinction (§4), do.

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
   `capabilities.service_extensions`. Going forward the reconciler consumes
   the whole spec — the design intent the fields were waiting on.
4. **Which exist only for documentation?** Two: `docs` and `semantics`, and
   both should be dropped (`semantics` only after `generated_by` is
   versioned, since its URL is currently the sole record of the generating
   version). v1's longer list (`generated_by`, `knowledge_adapter`) was
   wrong: both feed regeneration.
5. **Can existing metadata be simplified?** Marginally (drop two constants,
   one rename-and-collapse) — but the accurate statement is that it must be
   *completed*: `project.language` and `project.framework` are missing, and
   without them the manifest cannot distinguish a Python service from a Go
   one.
6. **Should knowledge adapters be a plugin/export mechanism?** The *adapter
   outputs* (Backstage/Obsidian files) are export-shaped, but the field stays
   in the manifest: it selects generated files, so the reconciler needs it.
7. **Should provider-specific concepts move toward deployment artifacts?**
   Yes for runtime detail; `provider.targets` stays only as the coarse
   selector of which IaC templates the generated set contains.
8. **Is the semantics reference document still justified?** The prose doc yes,
   as commentary; the per-repo `semantics` URL field no — after its version
   datum migrates to `generated_by`. The JSON Schema becomes the structural
   authority.
9. **Should project kinds be simplified — is "worker" a kind?** Not a kind: an
   execution profile of `service`. Retire it and reconcile the docs.
10. **Is the long-term moat conformance rather than generation?** Yes, with an
    honest caveat: the moat is *earned* by solving co-owned-file
    reconciliation, which is greenfield, has named prerequisites (ownership
    classification, persisted render inputs, per-release template retrieval),
    and may land in the fallback posture (drift report + regenerate-into-a-
    branch) rather than the full merge. Sequence it — complete spec →
    read-only drift report → marker + structured-file prototype → go/no-go —
    rather than declaring it. Generation remains the on-ramp and the thing
    that makes the manifest trustworthy in the first place.

---

## Guiding Principle Applied

Every kept field answers "does this improve deterministic repository
scaffolding without making kickstart responsible for application behavior?"
with yes, for a stated reason: it selects generated files or content (the
mechanical gate), and any behavior it generates is a seed on a closed
allowlist, owned by the user from first commit (the mission gate). Every
rejected field fails one gate or the other — the runtime-semantics layer
describes behavior kickstart either does not generate or must not bless, and
the two dropped constants select nothing at all. The boundary is one
mechanical test plus one deliberate, narrow policy — named as such, so the
next proposal to widen it has to argue with the mission statement rather than
with a schema.
