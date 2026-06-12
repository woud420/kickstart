---
name: cut-release
description: Cut, tag, and verify a kickstart release. Use when asked to release, tag, bump, or ship a new kickstart version, or to retag the current release line after a same-version fix.
---

# Cut Release

## Use When

Use this skill when asked to release a new kickstart version, retag the
current release line, or prepare a release PR. The full policy is
`docs/release-policy.md`; this is the executable path through it.

## Versioned Release

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

5. Merge to `master`, then tag the merge commit and push the tag:

   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

6. Watch the release workflow: verify → package (PyPI) → binary
   (linux-x64, linux-arm64, macos-arm64 at py3.14) → GitHub Release →
   website deploy. All jobs must be green, including Deploy Website.

## Same-Version Updates

For docs, website copy, tests, or non-behavior fixes: do not bump the
version. Merge, then retag the current release line onto the new `master`
HEAD. Release assets are overwritten; PyPI publish skips existing artifacts.

## Rules

- Stable semver tags only (`vX.Y.Z`). Release candidates and build suffixes
  are rejected by CI.
- Only tag commits already merged to `master`; the workflow enforces this.
- PyPI artifacts are immutable. If a bad version shipped, fix forward with a
  new patch version instead of retagging it.
- Do not start the tag step until `make release-check` passes locally.

## Report Back

Report the tag, the release workflow run URL and per-job conclusions, and
the deployed website version (https://kickstart-cli.org must show the new
version after the workflow finishes).
