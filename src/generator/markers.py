"""Ownership fences for managed regions in generated files.

kickstart only ever writes inside its own fenced regions; everything outside
a fence is user-owned and never read for decisions or modified. Markers are
comments in the host format — invisible to readers, meaningful to tooling —
following the installer's shell-rc marker-block precedent and the
terraform-docs/doctoc idiom:

- markdown: ``<!-- kickstart:begin <artifact-id> -->`` / ``<!-- kickstart:end <artifact-id> -->``
- yaml:     ``# kickstart:begin <artifact-id>`` / ``# kickstart:end <artifact-id>``

Fenced regions are whole-block replaced, so users must not edit inside them.
Parsing is fail-closed: duplicated, nested, mismatched, or out-of-order
markers raise ``MarkerError`` instead of guessing. A file with no markers for
an artifact is a pre-marker file (``find_fenced_region`` returns ``None``) —
callers report that as a structural fact, never as content drift.

Design rationale and the MDX v2 caveat live in
``docs/decisions/docs-ownership-fences.md``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from src.utils.errors import MarkerError

MarkerStyle = Literal["markdown", "yaml"]

# Marker ids are constrained so a hostile or malformed id cannot break out of
# the comment syntax or forge a different marker.
_ARTIFACT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")

# Line-leading marker prefixes in either style. Only full-line markers are
# meaningful to the parser, so prose that merely mentions the syntax mid-line
# is allowed; a line that opens like a marker is rejected fail-closed.
_MARKER_LINE_PREFIXES = (
    "<!-- kickstart:begin",
    "<!-- kickstart:end",
    "# kickstart:begin",
    "# kickstart:end",
)


@dataclass(frozen=True)
class FencedRegion:
    """One owned region inside a file: splice indices plus inner content."""

    artifact_id: str
    inner_start: int
    inner_end: int
    inner: str


def begin_marker(artifact_id: str, style: MarkerStyle = "markdown") -> str:
    """Return the begin marker line (without trailing newline)."""
    return _marker_line("begin", artifact_id, style)


def end_marker(artifact_id: str, style: MarkerStyle = "markdown") -> str:
    """Return the end marker line (without trailing newline)."""
    return _marker_line("end", artifact_id, style)


def fence(artifact_id: str, content: str, style: MarkerStyle = "markdown") -> str:
    """Wrap rendered content in its ownership fence.

    The content must not itself contain kickstart marker lines (fences do not
    nest; mid-line mentions of the syntax are fine), and always ends with
    exactly the newline the fence expects.
    """
    content = _prepared_content(artifact_id, content)
    return f"{begin_marker(artifact_id, style)}\n{content}{end_marker(artifact_id, style)}\n"


def find_fenced_region(text: str, artifact_id: str, style: MarkerStyle = "markdown") -> FencedRegion | None:
    """Locate the owned region for an artifact id, fail-closed.

    Returns ``None`` when neither marker is present (a pre-marker file).
    Raises ``MarkerError`` for every malformed shape: a lone begin or end,
    duplicated markers, end before begin, or another kickstart marker nested
    inside the region.
    """
    begin_line = begin_marker(artifact_id, style)
    end_line = end_marker(artifact_id, style)
    begin_matches = _marker_line_positions(text, begin_line)
    end_matches = _marker_line_positions(text, end_line)

    if not begin_matches and not end_matches:
        return None
    if len(begin_matches) > 1 or len(end_matches) > 1:
        raise MarkerError(f"duplicated kickstart markers for '{artifact_id}'")
    if not begin_matches or not end_matches:
        raise MarkerError(f"unpaired kickstart marker for '{artifact_id}'")

    inner_start = begin_matches[0][1]
    inner_end = end_matches[0][0]
    if inner_end < inner_start:
        raise MarkerError(f"kickstart end marker precedes begin marker for '{artifact_id}'")

    inner = text[inner_start:inner_end]
    if _contains_marker_line(inner):
        raise MarkerError(f"nested kickstart marker inside the '{artifact_id}' region")
    return FencedRegion(artifact_id=artifact_id, inner_start=inner_start, inner_end=inner_end, inner=inner)


def replace_fenced_region(text: str, artifact_id: str, content: str, style: MarkerStyle = "markdown") -> str:
    """Return text with the artifact's owned region replaced by new content.

    Everything outside the fence is preserved byte-for-byte. Raises
    ``MarkerError`` when the region is absent or malformed.
    """
    region = find_fenced_region(text, artifact_id, style)
    if region is None:
        raise MarkerError(f"no kickstart fence for '{artifact_id}' to replace")
    content = _prepared_content(artifact_id, content)
    return text[: region.inner_start] + content + text[region.inner_end :]


def _marker_line(kind: str, artifact_id: str, style: MarkerStyle) -> str:
    if _ARTIFACT_ID_PATTERN.fullmatch(artifact_id) is None:
        raise MarkerError(
            f"invalid artifact id '{artifact_id}': use lowercase letters, digits, and dashes"
        )
    label = f"kickstart:{kind} {artifact_id}"
    if style == "markdown":
        return f"<!-- {label} -->"
    return f"# {label}"


def _prepared_content(artifact_id: str, content: str) -> str:
    """Normalize owned-region content: newline-terminated, no marker lines."""
    if _contains_marker_line(content):
        raise MarkerError(
            f"content for '{artifact_id}' contains a kickstart marker line; fences do not nest"
        )
    if not content.endswith("\n"):
        content += "\n"
    return content


def _contains_marker_line(content: str) -> bool:
    """Return True when a line opens like a kickstart marker in either style."""
    return any(line.strip().startswith(_MARKER_LINE_PREFIXES) for line in content.splitlines())


def _marker_line_positions(text: str, marker_line: str) -> list[tuple[int, int]]:
    """Return (start, end-after-newline) spans of lines that are exactly the marker."""
    pattern = re.compile(rf"^{re.escape(marker_line)}[ \t]*\r?(?:\n|\Z)", re.MULTILINE)
    spans: list[tuple[int, int]] = []
    for match in pattern.finditer(text):
        spans.append((match.start(), match.end()))
    return spans
