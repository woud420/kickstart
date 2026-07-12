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
4. Regenerate the committed golden fixture (procedure in
   `docs/contributing.md`). The version bump changes the `semantics` URL
   inside the fixture's `.kickstart/scaffold.json`, so `make check` fails
   with a golden-fixture diff until the fixture is regenerated — this is
   expected, not a template bug.
5. Verify everything locally:

   ```bash
   make check
   cd website && bun run check && cd ..
   make release-check TAG=vX.Y.Z
   ```

6. Merge to `master`. The `Auto Tag Release` workflow tags the merge commit
   automatically when the `RELEASE_TAG_TOKEN` secret is configured (it
   re-runs `make release-check` first and never moves an existing tag).
   Without the secret the workflow fails — tag and push manually, pointing
   the tag at the version-bump merge commit (never bare `git tag` on a
   checkout whose HEAD may have advanced past the bump):

   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z" <version-bump-merge-commit>
   git push origin vX.Y.Z
   ```

7. Watch the release workflow: verify (incl. the website version-sync
   gate) → package → binary (linux-x64, linux-arm64, macos-arm64 at
   py3.14) → GitHub Release → website deploy. All jobs must be green,
   including Deploy Website.
8. Confirm the release is not stranded before reporting done:
   `git ls-remote --tags origin` lists `vX.Y.Z`, the GitHub Release for
   the tag exists, and https://kickstart-cli.org shows the new version.
   A merged bump with no tag blocks all same-version retags until fixed.

## Same-Version Updates

For docs, website copy, tests, or non-behavior fixes: do not bump the
version. Merge, then retag the current release line onto the new `master`
HEAD. Release assets are overwritten.

Precondition: the current version must actually be tagged. A
merged-but-untagged version bump makes every same-version retag fail
`release-check` (each post-bump commit carries the pending version) — tag
the pending version first.

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
