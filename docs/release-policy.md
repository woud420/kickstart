# Release Policy

kickstart releases are stable semantic version tags only:

```text
vMAJOR.MINOR.PATCH
```

Examples: `v0.4.0`, `v0.4.1`, `v0.4.2`.

The tag version must match `[project].version` in `pyproject.toml`, and `pyproject.toml` must agree with the runtime `src/__init__.py:__version__` (the constant `kickstart version` reports). Tags such as `v0.4`, `v0.4.1-rc.1`, and `v0.4.1+build.1` are rejected by CI, and so are desynced version files.

Validate the release tag locally with:

```bash
make release-check TAG=v0.4.1
```

## Versioned Releases

Use a new version when generated behavior, installable output, public CLI behavior, or release assets change.

1. Update `pyproject.toml` and `src/__init__.py:__version__` together.
2. Add the release entry to `CHANGELOG.md` and `website/src/site/content.ts` (the website tests fail when the current version has no release note; they run in `bun run check`, per-PR CI, and the release workflow's verify job before anything publishes).
3. Regenerate the committed golden fixture (procedure in [docs/contributing.md](contributing.md)) — the version bump changes the `semantics` URL inside the fixture's `.kickstart/scaffold.json`, so `make check` fails until the fixture matches.
4. Merge the change to `master`.
5. The `Auto Tag Release` workflow tags the merge commit with `vX.Y.Z` automatically when the `RELEASE_TAG_TOKEN` secret (fine-grained PAT, `contents: read/write`) is configured. It never moves an existing tag and only tags after `make release-check` passes. Without the secret the workflow **fails** (it used to skip on a green run, which stranded v0.4.3 untagged for two weeks) — tag and push manually instead, pointing the tag at the **version-bump merge commit**, not `master` HEAD, which may have advanced past the bump and would ship changes the changelog does not cover:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z" <version-bump-merge-commit>
git push origin vX.Y.Z
```

The tag push uses a PAT because tags pushed with the default `GITHUB_TOKEN` do not trigger the release workflow.

6. Verify the release actually shipped before calling it done: `git ls-remote --tags origin` shows the new tag, the release workflow ran green end to end (including Deploy Website), and kickstart-cli.org shows the new version. The weekly `Scheduled Evals` workflow also runs a release-drift check that fails whenever `pyproject.toml` names a version with no matching tag or GitHub Release.

The release workflow builds the Python package and Python 3.14 binary archives (`kickstart-<platform>-py3.14.tar.gz` for `linux-x64`, `linux-arm64`, and `macos-arm64`), publishes or updates the GitHub Release, and deploys the website with metadata for that tag.

## Same-Version Updates

For documentation, website copy, tests, or non-behavior fixes that should stay on the current version, do not create a new version number.

Retag the current release line after the fix is merged. The release workflow updates the existing GitHub Release for that tag, overwrites GitHub Release assets, and refreshes generated release notes.

Caveat: a merged-but-untagged version bump blocks same-version retags. `release-check` compares the tag against `pyproject.toml` at the tagged commit, and every commit after the bump carries the new version — so no fix can reach the published release or the website until the pending version is tagged. Tag the pending version first.

## Website

The website deploys for every stable release tag, including patch tags such as `v0.4.1`. Local commits and branch pushes do not update the public release metadata.

The deploy job runs with `ALCHEMY_CI_STATE_STORE_CHECK=false`: the Worker and its custom domain use `adopt: true`, so each deploy converges on the same named resources and ephemeral CI state cannot orphan infrastructure. Configure the optional `ALCHEMY_PASSWORD` and `ALCHEMY_STATE_TOKEN` repository secrets to upgrade deploys to the persistent Cloudflare state store.
