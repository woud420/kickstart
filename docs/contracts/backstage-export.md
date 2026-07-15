# Backstage Export

Checked: 2026-07-15

`kickstart export backstage [REPO]` writes or refreshes `catalog-info.yaml`
deterministically from `.kickstart/scaffold.json`. The mapping is the verb's;
human judgment (real owner, lifecycle, description) belongs to the
`backstage-catalog` skill layered on top.

## Field classes

- **Derived** — always regenerated, inside `# kickstart:begin/end` YAML
  fences: `apiVersion`, `kind`, `metadata.name` (the manifest's project
  name), `metadata.annotations.backstage.io/techdocs-ref: dir:.` when `docs/`
  exists, and `metadata.tags` (service extensions plus execution models,
  sorted). Systems additionally derive a `System` entity and, at creation,
  one child `Component` per contained project found through the manifest's
  `composition.child_manifest_globs`, each with `spec.system` set.
- **Declared** — emitted once with anonymous, catalog-valid defaults, then
  user-owned and never rewritten: `spec.type` (from the kind mapping:
  service/worker → `service`, frontend → `website`, library → `library`,
  cli → `tool`, system → `system`), `spec.lifecycle: experimental`, and
  `spec.owner: group:default/unknown`. Backstage requires owner and
  lifecycle to exist, so unknown values get sentinels, never empties. The
  owner sentinel is one shared constant across the `--knowledge backstage`
  system template, the exporter, and the skill.
- **Passthrough** — everything else outside the fences (user-added keys,
  descriptions, links) is never read for decisions and never rewritten.

## Re-export semantics

Repeated exports are idempotent: only fenced regions are spliced, so
`export → export` is byte-stable and user edits outside fences always
survive. An existing `catalog-info.yaml` with no kickstart fence is refused,
never overwritten. Child Components are created with the file; children added
to the system later are not auto-inserted on refresh (re-create or add by
hand) — a documented v1 limit. `spec.type` is derived at creation and then
preserved: a project-kind change requires re-creating the file.

## Exit codes

0 = exported cleanly (created/updated/unchanged); 1 = refused (unfenced or
malformed existing file) or exported with validation warnings (a required
entity line is missing after user edits); 2 = usage error (no repository or
no usable manifest). Obsidian export is a planned follow-up.
