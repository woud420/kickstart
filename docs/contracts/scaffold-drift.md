# Scaffold drift check

`kickstart drift REPO [--json]` checks the managed envelope recorded in a
schema-4 manifest without writing, regenerating application code or running
repository commands. It reuses the ownership and managed-doc projection libraries.

## Coverage

Only recorded non-seed paths are inspected. Missing ownership is reported as
unavailable coverage; current files never establish historical ownership. Seed
contents, unlisted files and user prose outside managed fences are excluded from
comparisons. Targets outside the repository or through unresolvable links are
reported unreadable.

| Class | Scope | Comparison |
| --- | --- | --- |
| `scaffold` | Manifest shape, agent map and agent guidance fences | Schema validation or current managed render |
| `docs` | Recorded documentation fences | Current managed render; architecture fence presence only |
| `ci` | Recorded workflow files | YAML structure and standard job identity |
| `artifact` | Recorded Makefile | Literal `check` target declaration, including target lists |

CI checks the declared `check` job in `ci.yml`, `workspace` in `build.yml`,
`generated-contracts` in `test.yml`, and `plan` in `deploy.yml`. Other recorded
workflow names must declare a nonempty jobs mapping. Duplicate root/job keys and
unparseable YAML produce findings. YAML is composed into nodes without constructing
Python objects.

These are structural facts. The checker does not validate GitHub Actions semantics,
evaluate conditions, inspect command behavior, compare recipes or claim a workflow
will run. A customized job or recipe body is preserved and never content-diffed.
There is no original generated base to reconstruct; managed regions compare with
the current standard. Broader reconciliation, repair and three-way merging remain
outside this command.

## Findings and machine-readable output

Statuses `in-sync` and `presence-only` pass. Findings are:

- `missing`: a recorded managed target is absent.
- `changed`: a managed fence differs from the current render; the diff contains
  only that fence's contents.
- `stale`: a required fence, literal target or standard workflow job is missing,
  malformed or no longer structurally usable.
- `unreadable`: a target is inaccessible, outside the root or invalid UTF-8.

JSON includes `root`, `recorded`, `in_sync`, `seeds_excluded`, `detail`, and
`entries`. Each entry has `class`, `target`, `status`, `check`, `detail` and
`diff`. Entries follow deterministic recorded-path order. An empty recorded scope
passes; it means only that declared scope passes. It does not establish repository
conformance.

Exit 0 means the recorded scope passes, 1 means findings or unavailable ownership
coverage, and 2 means no usable repository or manifest. Legacy 3.x manifests and
schema-4 manifests without ownership produce explicit unrecorded reports, never an
inferred index. Use the standalone command when CI requires recorded drift coverage.

## Adoption reuse

`kickstart adopt REPO --check` retains its independent conformance checks and adds
the same drift report when a valid manifest is present. JSON adds a `drift` field:
`null` without a usable manifest, otherwise the standalone report's payload.
Recorded drift findings make `complete` false and exit 1 even if the achieved and
claimed conformance levels are both `managed`.

For compatibility, unrecorded ownership does not fail adoption's conformance
result; its nested drift report explicitly shows unavailable coverage. No-manifest
repositories retain their vendor-neutral conformance path. Conformance may check
standard artifacts outside the recorded drift scope; its presence/fence checks are
distinct from the bounded drift comparison.

`kickstart plan` remains the existing docs-only view, and `plan --ownership`
retains its earlier bounded presence policy. The standalone drift command adds
normalized finding classes and workflow job structure checks.
