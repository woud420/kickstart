---
name: backstage-catalog
description: Derive a Backstage catalog-info.yaml from a kickstart-generated repo's .kickstart/scaffold.json. Use when asked to register a scaffolded or adopted project in a Backstage software catalog.
---

# Backstage Catalog Mapping

## Overview

Use this skill when asked to add a kickstart-generated (or adopted) repo to
a Backstage catalog. The mapping is derived from `.kickstart/scaffold.json`,
so the catalog entry stays consistent with the scaffold contract instead of
being hand-written.

Catalog metadata is opt-in: `system` scaffolds created with
`--knowledge backstage` already emit `catalog-info.yaml` and
`backstage_template.yaml` — check for them first and update rather than
duplicate. All other project kinds get their entry from this mapping.

## Workflow

1. Check the repo root for an existing `catalog-info.yaml` (and, for
   systems, `backstage_template.yaml`). If present, update it — show the
   diff before overwriting anything.
2. Read `.kickstart/scaffold.json` and apply the mapping table below to
   emit `catalog-info.yaml` at the repo root.
3. For `project.kind: system`, also emit the per-project `Component`
   entries described under the mapping table.
4. Ask the user for `spec.owner` if not stated; default
   `group:default/platform`.
5. Run the checks in Validation, then report back.

## Mapping

Read `.kickstart/scaffold.json` and emit `catalog-info.yaml` at the repo
root:

| catalog-info field | source |
| --- | --- |
| `apiVersion` | `backstage.io/v1alpha1` |
| `kind` | `Component` (`System` additionally for `project.kind: system`) |
| `metadata.name` | `project.name` (already DNS-label safe) |
| `metadata.description` | `kickstart-generated <project.kind>` unless the README gives a better one-liner |
| `metadata.annotations` | `backstage.io/techdocs-ref: dir:.` when `docs/` exists |
| `metadata.tags` | `capabilities.service_extensions` values (for example `postgres`, `redis`, `jwt`) plus `execution.models` entries |
| `spec.type` | `service` → `service`, `frontend` → `website`, `lib` → `library`, `cli` → `tool`, `system` → `system` |
| `spec.lifecycle` | `experimental` unless the user states otherwise |
| `spec.owner` | ask the user; default `group:default/platform` (matches the system template) |

For `system` repos, also emit one `Component` per contained project listed
in the scaffold's composition metadata, each with `spec.system` set to the
system's name.

## Rules

- Derive from `.kickstart/scaffold.json`; do not guess fields the scaffold
  does not state — omit them or ask.
- Never overwrite an existing `catalog-info.yaml` without showing the diff.
- Keep names DNS-label safe (lowercase alphanumerics and dashes).
- Validate the result parses as YAML and has `apiVersion`, `kind`,
  `metadata.name`, `spec.type`, `spec.lifecycle`, and `spec.owner` before
  reporting done.

## Validation

Before reporting done, confirm:

- `catalog-info.yaml` exists at the repo root and parses as YAML.
- `apiVersion`, `kind`, `metadata.name`, `spec.type`, `spec.lifecycle`,
  and `spec.owner` are all present.
- `metadata.name` equals `project.name` from `.kickstart/scaffold.json`
  and matches `^[a-z0-9-]+$` (the same pattern the generated
  `backstage_template.yaml` enforces).
- `backstage.io/techdocs-ref` is set only when `docs/` actually exists.
- For `system` repos: every contained project from the composition
  metadata has a `Component` entry with `spec.system` set to the system's
  name.
- If the scaffold already shipped catalog files (`--knowledge backstage`),
  the existing files were updated in place, not duplicated.

## Anti-Patterns

- Hand-writing catalog metadata instead of deriving it from
  `.kickstart/scaffold.json` — the entry drifts from the scaffold contract.
- Guessing fields the scaffold does not state; omit them or ask the user.
- Overwriting an existing `catalog-info.yaml` without showing the diff
  first.
- Emitting a second `catalog-info.yaml` or `backstage_template.yaml` in a
  `system` repo that was created with `--knowledge backstage` — update the
  existing files.
- Adding `backstage.io/techdocs-ref` when the repo has no `docs/`
  directory.
- Names that are not DNS-label safe (uppercase, underscores, dots).
- Inventing an owner or lifecycle: default `spec.owner` to
  `group:default/platform` and `spec.lifecycle` to `experimental` only as
  stated defaults, and prefer asking the user.

## Report Back

Report the emitted file path, the kind/type/owner chosen, and any scaffold
fields that had no catalog equivalent.
