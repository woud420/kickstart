"""Render the GitHub Release body for a tag from CHANGELOG.md.

The release page shows the summary paragraph that opens the version's
CHANGELOG section, a link to the full notes, and a short install note.
GitHub appends its generated list of merged pull requests below it.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


VERSION_HEADING = re.compile(r"^## v(?P<version>\S+)(?: - .*)?$", re.MULTILINE)
NEXT_HEADING = re.compile(r"^#{2,3} ", re.MULTILINE)
STABLE_TAG = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")


def changelog_summary(changelog: str, version: str) -> str:
    """Return the summary paragraph that opens a version's CHANGELOG section."""
    for match in VERSION_HEADING.finditer(changelog):
        if match.group("version") != version:
            continue
        rest = changelog[match.end() :]
        next_heading = NEXT_HEADING.search(rest)
        section = rest[: next_heading.start()] if next_heading else rest
        paragraph = section.strip().split("\n\n", 1)[0].strip()
        if paragraph == "":
            raise ValueError(f"CHANGELOG.md section for v{version} has no summary paragraph")
        return " ".join(line.strip() for line in paragraph.splitlines())
    raise ValueError(f"CHANGELOG.md has no section for v{version}")


def release_body(changelog: str, tag: str, repository: str) -> str:
    """Return the Markdown body for the GitHub Release of a stable tag."""
    match = STABLE_TAG.match(tag)
    if match is None:
        raise ValueError(f"{tag!r} is not a stable release tag (vX.Y.Z)")
    summary = changelog_summary(changelog, match.group("version"))
    blob = f"https://github.com/{repository}/blob/{tag}"
    return f"""{summary}

Full notes: [CHANGELOG.md]({blob}/CHANGELOG.md).

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/{repository}/master/scripts/install.sh | bash
```

The archives below cover `linux-x64`, `linux-arm64` and `macos-arm64`. On other
platforms use `pipx install git+https://github.com/{repository}`; the PyPI
package named `kickstart` is an unrelated project. Release builds send
pseudonymous usage telemetry by default, and `kickstart telemetry disable`
turns it off. The [install runbook]({blob}/docs/operations/install-binaries.md)
covers manual installs, custom paths and checksums.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repository", required=True, help="owner/name")
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    body = release_body(args.changelog.read_text(encoding="utf-8"), args.tag, args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(body, encoding="utf-8")
    print(f"Wrote {args.output} for {args.tag}")


if __name__ == "__main__":
    main()
