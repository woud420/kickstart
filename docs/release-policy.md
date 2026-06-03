# Release Policy

kickstart releases are stable semantic version tags only:

```text
vMAJOR.MINOR.PATCH
```

Examples: `v0.4.0`, `v0.4.1`, `v0.4.2`.

The tag version must match `[project].version` in `pyproject.toml`. Tags such as `v0.4`, `v0.4.1-rc.1`, and `v0.4.1+build.1` are rejected by CI.

Validate the release tag locally with:

```bash
make release-check TAG=v0.4.1
```

## Versioned Releases

Use a new version when generated behavior, installable output, public CLI behavior, or release assets change.

1. Update `pyproject.toml`.
2. Merge the change to `master`.
3. Tag the merged commit with `vX.Y.Z`.
4. Push the tag.

The release workflow builds the Python package and Linux/macOS binary archives (`kickstart-<platform>-py<minor>.tar.gz`, one per supported Python minor), publishes or updates the GitHub Release, and deploys the website with metadata for that tag.

## Same-Version Updates

For documentation, website copy, tests, or non-behavior fixes that should stay on the current version, do not create a new version number.

Retag the current release line after the fix is merged. The release workflow updates the existing GitHub Release for that tag, overwrites GitHub Release assets, and refreshes generated release notes. PyPI publish uses `--skip-existing`, so existing package artifacts for that version are skipped (no overwrite).

## Website

The website deploys for every stable release tag, including patch tags such as `v0.4.1`. Local commits and branch pushes do not update the public release metadata.
