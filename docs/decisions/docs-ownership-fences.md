# Docs Ownership Fences

Checked: 2026-07-15

## Bottom Line

Managed docs projections are wrapped in ownership fences — comment markers in
the host file format — and kickstart only ever writes inside its own fences.
Markdown uses HTML comments (`<!-- kickstart:begin <artifact-id> -->` /
`<!-- kickstart:end <artifact-id> -->`); YAML uses `#` comments. Fenced
regions are whole-block replaced, so users must not edit inside them; content
outside a fence is user-owned and never read or rewritten.

## Why Host-Format Comments

The rule generalizes across file types with one principle: **markers are
comments in the host format** — invisible to readers, meaningful to tooling.

- The installer uses the same principle for shell rc files
  (`src/utils/installer.py` marker blocks), including its documented limit:
  whole-block replacement clobbers edits inside the region, which is why the
  region is declared not-user-editable rather than merged. The mechanisms are
  deliberately separate implementations — the installer's block is anonymous,
  single-region, and permissive-idempotent; these fences are id-scoped,
  multi-region, and fail-closed.
- Ecosystem precedent for markdown is heavy: `terraform-docs`
  (`<!-- BEGIN_TF_DOCS -->`), `doctoc`, all-contributors, GitHub README
  injectors.

## Alternatives Rejected

- **Code blocks** change what the content is: anything inside triple-backtick
  fences renders as literal monospace text, so bullets stop being lists and
  links stop being clickable. Code blocks display code; they do not delimit
  prose regions.
- **YAML frontmatter** exists once per file, only at the top, and is metadata
  about the file — it cannot delimit multiple regions or mid-file blocks, and
  GitHub renders it visibly as a table.

## Fail-Closed Parsing

`src/generator/markers.py` refuses to guess: duplicated, unpaired,
out-of-order, or nested markers raise `MarkerError`. A file with no markers
for an artifact is a pre-marker file — tooling reports that as a structural
fact, never as content drift and never by rewriting user content.

## Known Caveat: MDX

MDX v2+ rejects HTML comments, so a `docs/` tree ingested raw by an MDX-based
site would need the markers translated at that boundary. This is rare for
plain repo docs and deliberately accepted. Recorded fallbacks if it ever
binds: a configurable marker syntax, or per-file ownership (a wholly
generated file the README links to) — neither changes the ownership model.
