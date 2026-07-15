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

# Exact marker lines, matched against a line with its newline stripped.
_MARKDOWN_MARKER_PATTERN = re.compile(r"<!-- kickstart:(begin|end) ([a-z0-9][a-z0-9-]*) -->[ \t]*")
_YAML_MARKER_PATTERN = re.compile(r"# kickstart:(begin|end) ([a-z0-9][a-z0-9-]*)[ \t]*")


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
    """Locate the owned region for an artifact id, fail-closed across the file.

    The whole file's marker universe is validated first: every marker-like
    line anywhere must be an exact, unindented kickstart marker, and the full
    set must form ordered, non-overlapping begin/end pairs. Any stray,
    partial, duplicated, reversed, or nested marker — for this artifact or
    any other — raises ``MarkerError``; ownership decisions never run against
    an ambiguous file. Returns ``None`` when the file has no region for this
    artifact (a pre-marker file or a different artifact's file).
    """
    _validate_artifact_id(artifact_id)
    return _validated_regions(text).get((style, artifact_id))


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
    _validate_artifact_id(artifact_id)
    label = f"kickstart:{kind} {artifact_id}"
    if style == "markdown":
        return f"<!-- {label} -->"
    return f"# {label}"


def _validate_artifact_id(artifact_id: str) -> None:
    if _ARTIFACT_ID_PATTERN.fullmatch(artifact_id) is None:
        raise MarkerError(
            f"invalid artifact id '{artifact_id}': use lowercase letters, digits, and dashes"
        )


@dataclass(frozen=True)
class _MarkerLine:
    """One exact marker line found in a file."""

    kind: str
    style: MarkerStyle
    artifact_id: str
    start: int
    end: int


def _marker_universe(text: str) -> list[_MarkerLine]:
    """Parse every marker-like line in the file, fail-closed.

    A line that looks like a kickstart marker but is not an exact, unindented
    marker line is an error wherever it appears — inside or outside any
    region — so a stray or mangled marker can never be silently ignored.
    """
    markers: list[_MarkerLine] = []
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line_start = offset
        offset += len(raw_line)
        content = raw_line.rstrip("\r\n")
        if not content.strip().startswith(_MARKER_LINE_PREFIXES):
            continue
        if content != content.lstrip(" \t"):
            raise MarkerError(f"indented kickstart marker-like line: {content.strip()!r}")
        parsed = _parse_marker_line(content)
        if parsed is None:
            raise MarkerError(f"marker-like line is not a valid kickstart marker: {content!r}")
        kind, style, parsed_id = parsed
        markers.append(_MarkerLine(kind=kind, style=style, artifact_id=parsed_id, start=line_start, end=offset))
    return markers


def _parse_marker_line(content: str) -> tuple[str, MarkerStyle, str] | None:
    markdown = _MARKDOWN_MARKER_PATTERN.fullmatch(content)
    if markdown is not None:
        return markdown.group(1), "markdown", markdown.group(2)
    yaml = _YAML_MARKER_PATTERN.fullmatch(content)
    if yaml is not None:
        return yaml.group(1), "yaml", yaml.group(2)
    return None


def _validated_regions(text: str) -> dict[tuple[MarkerStyle, str], FencedRegion]:
    """Validate the file's whole marker set and return its regions by (style, id)."""
    grouped: dict[tuple[MarkerStyle, str], list[_MarkerLine]] = {}
    for marker in _marker_universe(text):
        grouped.setdefault((marker.style, marker.artifact_id), []).append(marker)

    regions: dict[tuple[MarkerStyle, str], FencedRegion] = {}
    spans: list[tuple[int, int, str]] = []
    for (style, artifact_id), lines in grouped.items():
        if [line.kind for line in lines] != ["begin", "end"]:
            raise MarkerError(
                f"kickstart markers for '{artifact_id}' are not exactly one ordered begin/end pair"
            )
        begin, end = lines
        regions[(style, artifact_id)] = FencedRegion(
            artifact_id=artifact_id,
            inner_start=begin.end,
            inner_end=end.start,
            inner=text[begin.end : end.start],
        )
        spans.append((begin.start, end.end, artifact_id))

    spans.sort()
    for (_, previous_end, previous_id), (next_start, _, next_id) in zip(spans, spans[1:]):
        if next_start < previous_end:
            raise MarkerError(f"kickstart regions '{previous_id}' and '{next_id}' overlap")
    return regions


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


