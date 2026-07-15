---
name: backstage-catalog
description: Register a kickstart-generated or adopted repo in a Backstage software catalog using the deterministic `kickstart export backstage` verb, then fill in the human judgment fields. Use when asked to add a scaffolded or adopted project to Backstage.
---

# Backstage Catalog Registration

## Use When

Use this skill when asked to add a kickstart-generated (or adopted) repo to a
Backstage catalog. The mechanical mapping is owned by the deterministic verb —
never hand-derive it; this skill supplies the judgment the verb deliberately
does not.

## Procedure

1. Run `kickstart export backstage <repo>`. It derives `catalog-info.yaml`
   from `.kickstart/scaffold.json`: derived fields (apiVersion, kind,
   metadata name/tags/techdocs annotation, and for systems the System entity
   plus child Components) sit inside `# kickstart:begin/end` fences and
   refresh on every run; `spec.type`, `spec.lifecycle: experimental`, and
   `spec.owner: group:default/unknown` are emitted once as anonymous
   defaults and then belong to the user.
2. Review the diff. Never overwrite by hand what the verb owns (inside the
   fences); never let the verb own what humans decide (outside them). An
   existing hand-written `catalog-info.yaml` is refused by the verb —
   migrate it by moving its human fields outside a fresh export's fences.
3. Fill in the judgment fields outside the fences:
   - `spec.owner`: ask the user; replace the `group:default/unknown`
     sentinel with the real owning group.
   - `spec.lifecycle`: keep `experimental` unless the user states otherwise.
   - `metadata.description`: add a one-liner if the README gives a better
     one than none.
4. Validate: the file parses as YAML and every entity has `apiVersion`,
   `kind`, `metadata.name`, `spec.type`, `spec.lifecycle`, `spec.owner`
   (the verb warns on missing required lines — resolve warnings before
   reporting done).

## Rules

- The verb is the source of truth for derived fields; do not guess fields
  the scaffold does not state — omit them or ask.
- Keep names DNS-label safe (lowercase alphanumerics and dashes).
- Re-running the export must be a no-op when nothing changed; if it is not,
  something edited inside a fence — restore via re-export and move the edit
  outside.

## Report Back

Report the file path, created/updated/unchanged, the owner and lifecycle
chosen, and any scaffold fields that had no catalog equivalent.
