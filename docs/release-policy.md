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
2. Add the release entry to `CHANGELOG.md` and `website/src/site/content.ts` (website tests fail when the current version has no release note).
3. Merge the change to `master`.
4. Tag the merged commit with `vX.Y.Z`.
5. Push the tag.

The release workflow builds the Python package and Python 3.14 binary archives (`kickstart-<platform>-py3.14.tar.gz` for `linux-x64`, `linux-arm64`, and `macos-arm64`), publishes or updates the GitHub Release, and deploys the website with metadata for that tag.

## Same-Version Updates

For documentation, website copy, tests, or non-behavior fixes that should stay on the current version, do not create a new version number.

Retag the current release line after the fix is merged. The release workflow updates the existing GitHub Release for that tag, overwrites GitHub Release assets, and refreshes generated release notes. PyPI publish uses `--skip-existing`, so existing package artifacts for that version are skipped (no overwrite).

## Website

The website deploys for every stable release tag, including patch tags such as `v0.4.1`. Local commits and branch pushes do not update the public release metadata.

The deploy job runs with `ALCHEMY_CI_STATE_STORE_CHECK=false`: the Worker and its custom domain use `adopt: true`, so each deploy converges on the same named resources and ephemeral CI state cannot orphan infrastructure. Configure the optional `ALCHEMY_PASSWORD` and `ALCHEMY_STATE_TOKEN` repository secrets to upgrade deploys to the persistent Cloudflare state store.
