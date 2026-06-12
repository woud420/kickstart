---
name: backstage-catalog
description: Derive a Backstage catalog-info.yaml from a kickstart-generated repo's .kickstart/scaffold.json. Use when asked to register a scaffolded or adopted project in a Backstage software catalog.
---

# Backstage Catalog Mapping

## Use When

Use this skill when asked to add a kickstart-generated (or adopted) repo to
a Backstage catalog. The mapping is derived from `.kickstart/scaffold.json`,
so the catalog entry stays consistent with the scaffold contract instead of
being hand-written.

Catalog metadata is opt-in: `system` scaffolds created with
`--knowledge backstage` already emit `catalog-info.yaml` and
`backstage_template.yaml` — check for them first and update rather than
duplicate. All other project kinds get their entry from this mapping.

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

## Report Back

Report the emitted file path, the kind/type/owner chosen, and any scaffold
fields that had no catalog equivalent.
