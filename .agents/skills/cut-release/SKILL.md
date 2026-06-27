---
name: cut-release
description: Cuts, tags, and verifies a kickstart release. Use when asked to release, tag, bump, or ship a new kickstart version, prepare a release PR, or retag the current release line after a same-version fix.
---

# Cut Release

## Overview

Use this skill when asked to release a new kickstart version, retag the
current release line, or prepare a release PR. The full policy is
`docs/release-policy.md`; this is the executable path through it.

## Workflow

### Versioned Release

1. Bump `pyproject.toml:[project].version` and `src/__init__.py:__version__`
   together. They must match — `ci/release_policy.py` fails the release when
   they disagree.
2. Add the release entry to `CHANGELOG.md` and to `releaseNotes` in
   `website/src/site/content.ts`, and bump `defaultProjectMeta.latestVersion`
   there. Website tests fail when the current version has no release note.
3. Update the dev-vars fallback in `website/wrangler.toml`
   (`PROJECT_VERSION`, `RELEASE_URL`) and the `defaultConfig` fallback in
   `website/scripts/render-release-config.ts`.
4. Verify everything locally:

   ```bash
   make check
   cd website && bun run check && cd ..
   make release-check TAG=vX.Y.Z
   ```

5. Merge to `master`. The `Auto Tag Release` workflow tags the merge commit
   automatically when the `RELEASE_TAG_TOKEN` secret is configured (it
   re-runs `make release-check` first and never moves an existing tag).
   Without the secret, tag and push manually:

   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

6. Watch the release workflow: verify → package (PyPI) → binary
   (linux-x64, linux-arm64, macos-arm64 at py3.14) → GitHub Release →
   website deploy. All jobs must be green, including Deploy Website.

### Same-Version Updates

For docs, website copy, tests, or non-behavior fixes: do not bump the
version. Merge, then retag the current release line onto the new `master`
HEAD. Release assets are overwritten; PyPI publish skips existing artifacts.

## Anti-Patterns

- Non-stable tags. Stable semver tags only (`vX.Y.Z`); release candidates
  and build suffixes are rejected by CI.
- Tagging a commit that is not already merged to `master`; the workflow
  enforces this.
- Retagging a version that already shipped to PyPI to fix it. PyPI artifacts
  are immutable — if a bad version shipped, fix forward with a new patch
  version instead of retagging it.
- Starting the tag step before `make release-check` passes locally.
- Bumping `pyproject.toml` without `src/__init__.py:__version__` (or vice
  versa) — `ci/release_policy.py` fails the release on a desync.
- Bumping the version for docs, website copy, tests, or non-behavior fixes —
  those are same-version updates; retag the current release line instead.

## Validation

The release is done only when all of the following hold:

- `make check`, `cd website && bun run check`, and
  `make release-check TAG=vX.Y.Z` all passed locally before tagging.
- The tag `vX.Y.Z` exists on the merged `master` commit and matches both
  `pyproject.toml:[project].version` and `src/__init__.py:__version__`.
- The release workflow run is fully green: verify, package (PyPI), binary
  (linux-x64, linux-arm64, macos-arm64 at py3.14), GitHub Release, and
  Deploy Website.
- https://kickstart-cli.org shows the new version after the workflow
  finishes.

## Report Back

Report the tag, the release workflow run URL and per-job conclusions, and
the deployed website version (https://kickstart-cli.org must show the new
version after the workflow finishes).
