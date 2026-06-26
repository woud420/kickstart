# Scaffold Metadata Architecture Review

Checked: 2026-06-26

Scope: evaluate the proposal to evolve `.kickstart/scaffold.json` from scaffold
metadata into a generalized "capability contract" describing runtime
operations, effects, policies, adapters, approvals, and retry semantics.

## Bottom Line

The capability-contract proposal should be **narrowed and renamed, not
implemented as described.** Abandon the runtime-semantics layer (effects,
policies, authorization, retry/idempotency declarations, tool registries,
workflow). Keep — and rename — only the narrow, already-shipping
`capabilities.service_extensions` field, because that is the one part backed by
real generated code.

The decisive evidence is consumption. Today's manifest already declares far
more than anything reads:

- The shipped tool reads exactly three keys, and only for presence:
  `schema_version`, `project`, `lifecycle` (`src/generator/adoption.py:92`).
- `execution`, `artifacts`, `provider`, `capabilities`, `composition` are read
  **only by internal eval scripts** (`scripts/scaffold_matrix_eval.py`,
  `scripts/bootstrap_eval.py`, `scripts/generated_make_test_eval.py`), never by
  a command a user runs.
- `generated_by`, `knowledge_adapter`, `docs`, `semantics` have **no reader
  anywhere** in `src/`. They are emitted-only.

A system that does not yet consume `retry_safe`-shaped *descriptive* fields it
already emits has no mechanism to make `retry_safe: true` *true*. Adding a
runtime contract layer would multiply the gap between what the manifest claims
and what the repo enforces. The guiding principle — "does this improve
deterministic repository scaffolding without making kickstart responsible for
application behavior?" — answers no for every runtime-semantics field in the
proposal.

The project's real, defensible direction is **deterministic repository
conformance** (`adopt`, drift, audit, repair), not a richer description
language. That is the "Terraform for repository structure" framing, and it is
correct.

---

## 1. Critique Of The Current Metadata Model

### 1.1 The manifest is overwhelmingly descriptive, not contractual

A "contract" implies a reader that enforces it. By that test, most of the
manifest is not a contract — it is generated documentation in JSON form. The
consumption map:

| Top-level key | Read by shipped tool? | Read by internal evals? | Read by export skill? | Verdict |
|---|---|---|---|---|
| `schema_version` | Yes — presence (`adoption.py:92`) | — | — | **Consumed** |
| `project` | Yes — presence (`adoption.py:92`) | kind/repo_layout | name/kind | **Consumed** |
| `lifecycle` | Yes — presence (`adoption.py:92`) | — | — | **Consumed** |
| `execution` | No | models/platforms | models→tags | Descriptive |
| `artifacts` | No | yes | — | Descriptive |
| `provider` | No | targets | — | Descriptive |
| `capabilities` | No | service_extensions (test coverage) | extensions→tags | Descriptive |
| `composition` (system) | No | repo_layout/validation | per-component | Descriptive |
| `generated_by` | No | No | No | **Emitted-only** |
| `knowledge_adapter` | No | No | No | **Emitted-only** |
| `docs` | No | No | presence only | **Emitted-only** |
| `semantics` | No | No | No | **Emitted-only** |

The internal evals are the only consumers of the "middle tier." That matters:
evals validate that generation is *self-consistent*, not that the metadata
*does* anything for a user. If a field exists solely so an eval can assert it
was emitted, it is documentation with a test, not a contract.

### 1.2 Two axes (`execution` vs `provider`) and a redundancy (`models` vs `platforms`)

`execution.models` and `execution.platforms` co-vary almost perfectly across
every construction site:

| project_kind | execution.models | execution.platforms |
|---|---|---|
| service (container) | `("container",)` | `("kubernetes",)` or `("local",)` |
| worker | `("cloudflare-worker",)` | `("cloudflare-workers",)` |
| frontend | `("static-site",)` | `("static-host",)` |
| library | `("library",)` | `("none",)` |
| cli | `("cli",)` | `("local",)` |

Only `service` varies its platform (helm → kubernetes), and only `system`
carries multi-valued sets. Two parallel vocabularies ("how it runs" vs "where
it runs") are conceptually clean but, in practice, one is derivable from the
other for every single-project kind. This is ontology for completeness, not for
consumption.

### 1.3 `capabilities` is misnamed today — before any proposal

The existing `capabilities` key contains exactly one thing:
`service_extensions: {database, cache, auth}`. These are **generation-time
options that produced real code** (Postgres/Redis/JWT wiring), validated
against a narrow support matrix in `src/generator/service_capabilities.py`. That
is a good, honest field. But it is not a "capability" in the
runtime/effect/authorization sense the proposal uses the word. The name already
invites the exact scope creep this review warns against — it is a pre-installed
on-ramp to "capability contracts."

### 1.4 `worker` is an ontology inconsistency that is live right now

`ProjectKind` includes `"worker"` and the generator emits
`project_kind: "worker"` for `kickstart service --runtime cloudflare-workers`
(`src/generator/service.py`). But:

- `worker` is **not** a CLI command — `KNOWN_PROJECT_TYPES` in
  `src/cli/dispatch.py` does not include it. Users reach it only through
  `service --runtime cloudflare-workers`.
- `README.md:10` advertises "workers" as a generated thing; `AGENTS.md:27`
  lists only `service, frontend, lib, cli, system` and calls
  `cloudflare-workers` a service *runtime*.

So the same concept is simultaneously "a runtime of service" (docs, CLI) and "a
project kind" (manifest, lifecycle/subjects branches). This is precisely the
kind of low-grade ontology drift that compounds. It is also the clearest
litmus test for the proposal: if we cannot keep one well-understood concept
consistent across CLI, manifest, and docs, we should not add a dozen runtime
concepts.

### 1.5 `semantics` and `docs` carry no information

`semantics` is a constant function of the version
(`SEMANTICS_REFERENCE = .../v{__version__}/docs/scaffold-contract.md`) and is
never read. `docs` is the same five hardcoded paths in every manifest and is
never read (adopt checks the directories on disk directly,
`adoption.py:28-38`). Both are pure constants serialized per repo.

---

## 2. Concepts To Remove, Merge, Or Rename

**Remove (emitted-only constants, zero readers):**

- `generated_by` — always `"kickstart"`. If provenance matters, fold into
  `schema_version` or a single `generator` string with a version.
- `semantics` — derivable from `schema_version`; stop serializing a constant
  URL into every repo.
- `docs` — the same five paths every time; `adopt` already inspects
  directories directly. Replace with nothing, or a single boolean if a reader
  ever needs it.

**Merge:**

- `execution.models` + `execution.platforms` → consider a single
  `runtime` profile per project, with platforms derived. At minimum, document
  that these are descriptive and stop treating them as independent inputs.
- `knowledge_adapter` → move out of core metadata into an **exporter/plugin**
  concern (see §3 and §6). It already only toggles optional external files and
  is read by nothing in core.

**Rename:**

- `capabilities` → `extensions` (or `selected_options`). Name it for what it
  is: generation-time options that produced code. This deliberately closes the
  semantic door the word "capabilities" leaves open.
- `project_kind: "worker"` → eliminate the kind. Model Cloudflare Workers as
  `kind: "service"` with an execution/runtime profile of `cloudflare-worker`.
  This removes the `worker` branches in `_lifecycle()` and `contract_subjects`
  and reconciles README/AGENTS/manifest.

**Keep (genuinely consumed or genuinely useful for conformance):**

- `schema_version`, `project`, `lifecycle` — consumed by `adopt`.
- `artifacts` — the best descriptor of generated files; high value for drift
  detection (see §5).

---

## 3. Architectural Boundary: What Kickstart Owns

**Kickstart owns the static shape of a repository and its conformance to a
standard.** It is Terraform for repository structure: it declares a desired
layout, generates it deterministically, and (the growth area) detects and
repairs drift from it.

| Kickstart OWNS | Kickstart does NOT own |
|---|---|
| Directory layout and standard files | Runtime behavior / execution |
| Generated docs scaffolding | API contracts (→ OpenAPI/AsyncAPI) |
| Lifecycle **verbs** (`make check`, etc.) | What those verbs *do* at runtime |
| Which generation-time extensions produced code | Effect systems / idempotency / retry semantics |
| CI workflow files | Authorization / policy (→ OPA) |
| Machine-readable scaffold manifest | Workflow orchestration (→ Temporal) |
| Conformance: adopt, drift, audit, repair, upgrade | Tool/operation registries (→ MCP, executor.sh) |
| **Exports** to the above ecosystems | Becoming any of the above ecosystems |

The boundary test: kickstart may *describe* a generated file and *check that it
still exists and matches*. It may not assert properties of code execution it
cannot generate and cannot verify. `retry_safe`, `idempotent`,
`requires_approval`, effects, and policies all fail this test — they are claims
about runtime behavior that the scaffold neither produces nor enforces.

---

## 4. Simplified Metadata Model

Target: every field is either consumed by the tool or directly useful for
conformance/drift. Illustrative service manifest:

```json
{
  "schema_version": "4.0",
  "generator": "kickstart@0.4.3",
  "project": {
    "name": "my-api",
    "kind": "service",
    "repo_layout": "single-project",
    "runtime": "container"
  },
  "lifecycle": {
    "install": "make install",
    "test": "make test",
    "check": "make check",
    "build": "make build",
    "dev": "make dev"
  },
  "artifacts": {
    "image": "dockerfile",
    "ci": "github-actions"
  },
  "extensions": {
    "database": "postgres",
    "cache": "redis",
    "auth": "jwt"
  }
}
```

Changes from 3.0:

- Dropped `generated_by`, `semantics`, `docs` (constants / no readers).
- Folded `execution`/`provider` into `project.runtime` for single-project
  kinds; keep an explicit multi-valued block only for `system` where it carries
  real variation.
- Renamed `capabilities.service_extensions` → top-level `extensions`.
- `worker` is no longer a kind; it is `kind: "service"`, `runtime:
  "cloudflare-worker"`, with `artifacts.worker: "wrangler"` and
  `provider: cloudflare` retained where they describe emitted files.
- `knowledge_adapter` removed from the core manifest; surfaced only when an
  exporter is active.

`system` keeps a `composition` block (it is the one place multi-runtime,
multi-provider variation is real), but `composition` should become consumed —
by drift detection over child manifests — rather than emitted-only.

The schema itself, not the prose doc, should be the source of truth: ship a
**JSON Schema** generated from the TypedDicts so agents validate structurally.
The prose `scaffold-contract.md` stays as commentary, not as the authority.

---

## 5. Roadmap

### Strengthen (the moat)

Repository conformance is currently thin: `adopt --check` verifies that nine
artifacts exist and that the manifest has three keys and the Makefile has a
`check` target (`src/generator/adoption.py`). Build it out:

- **Drift detection:** does the existing `scaffold.json` (and the files it
  describes) match what the current kickstart version would generate? This is
  `terraform plan` for repo structure and is the highest-leverage feature in
  the entire review.
- **Audit:** report scaffold drift, doc drift, CI drift, generated-artifact
  drift as distinct classes.
- **Repair / normalize:** apply the standard to a drifted repo (the explicit
  write step `adopt` is currently designed to defer).
- **Upgrade:** schema migration `3.0 → 4.0` with a documented, tested path.

### Simplify

- Remove `generated_by`, `semantics`, `docs` constants.
- Rename `capabilities` → `extensions`.
- Resolve the `worker` kind into `service` + runtime profile; reconcile
  README/AGENTS/manifest.
- Publish a JSON Schema as the structural source of truth.

### Remove (keep out of scope)

- Capability DSL, generalized effect systems, runtime semantic contracts.
- Policy/authorization engines, workflow/orchestration engines.
- Retry/idempotency/approval declarations.
- Tool/operation registries as first-class manifest concepts.

### Postpone

- **Exporters** (OpenAPI, MCP annotations, Backstage `catalog-info.yaml`,
  AsyncAPI). Valuable and on-mission *as derived projections*, but build them
  after the core is simplified and after drift detection lands. The existing
  `backstage-catalog` skill is the correct model: derive from `scaffold.json`
  plus generated code; never invent intermediate metadata. Exporters write
  *out* to existing ecosystems; they do not pull those ecosystems' concepts
  *in*.
- Provider-specific runtime concepts — keep these attached to deployment
  artifacts (Terraform/Wrangler files), not to repository metadata.

---

## 6. Recommendation On Capability Contracts

**Narrow + rename. Do not implement the proposed runtime-semantics layer.**

- **Abandon:** effects, policies, authorization, retry/idempotency/approval
  semantics, tool registries, workflow, generalized capability DSL. These
  belong to OpenAPI/AsyncAPI, MCP, OPA, and Temporal respectively; kickstart
  should *export to* them, not reimplement them.
- **Narrow:** the only "capability" with real backing is
  `service_extensions` — code kickstart actually generates and validates. Keep
  that and nothing more under this heading.
- **Rename:** call it `extensions` (or `selected_options`). The word
  "capability" is itself a scope-creep vector; removing it removes the
  temptation.
- **Reduced form, if anything:** if a future need for richer description
  appears, satisfy it with an **exporter** that derives an OpenAPI/MCP document
  from generated code — not with new intermediate manifest abstractions.

---

## Answers To The Specific Questions

1. **Is "capability" the right abstraction?** No. The only real instance is
   generated extensions; keep metadata scaffold-oriented.
2. **Would "operations" be better than "capabilities"?** No — "operations"
   implies runtime-invocable units (MCP/OpenAPI territory) and invites the same
   creep. Use `extensions`/`selected_options`.
3. **Which fields are consumed today?** By the shipped tool: `schema_version`,
   `project`, `lifecycle` (presence only). By internal evals: `execution`,
   `artifacts`, `provider`, `capabilities`, `composition`. By the Backstage
   skill: `project`, `execution.models`, `capabilities`, `docs`.
4. **Which exist only for documentation?** `generated_by`, `knowledge_adapter`,
   `docs`, `semantics` (no reader anywhere).
5. **Can existing metadata be simplified?** Yes — see §4. Drop 3 constants,
   merge execution/provider for single-project kinds, rename one field.
6. **Should knowledge adapters be a plugin/export mechanism?** Yes. Move out of
   core metadata; surface only when an exporter runs.
7. **Should provider-specific concepts move toward deployment artifacts?** Yes.
   Keep provider detail with the Terraform/Wrangler files it describes.
8. **Is the semantics reference document still justified?** The *document* yes
   (as commentary), but the per-repo `semantics` *URL field* should be dropped
   and a JSON Schema should become the structural source of truth.
9. **Should project kinds be simplified — is "worker" a kind?** No, `worker` is
   an execution/runtime profile of `service`, not a kind. Remove the kind and
   reconcile docs.
10. **Is the long-term moat conformance rather than generation?** Yes.
    Deterministic repository conformance (adopt/drift/audit/repair/upgrade) is
    the durable, defensible product. Generation is the on-ramp.

---

## Guiding Principle Applied

Every surviving field answers "does this improve deterministic repository
scaffolding without making kickstart responsible for application behavior?" with
yes: `schema_version`, `project`, `lifecycle`, `artifacts`, and narrowed
`extensions` describe static structure and generated files. Every removed field
either describes runtime behavior kickstart cannot enforce (the capability-
contract layer) or carries no information at all (the emitted-only constants).
