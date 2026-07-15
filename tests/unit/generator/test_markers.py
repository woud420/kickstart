"""Ownership fence markers: fail-closed parsing, splice-exact replacement."""

import pytest

from src.generator.markers import (
    begin_marker,
    end_marker,
    fence,
    find_fenced_region,
    replace_fenced_region,
)
from src.utils.errors import MarkerError


def test_marker_lines_are_host_format_comments() -> None:
    assert begin_marker("agent-map") == "<!-- kickstart:begin agent-map -->"
    assert end_marker("agent-map") == "<!-- kickstart:end agent-map -->"
    assert begin_marker("catalog", style="yaml") == "# kickstart:begin catalog"
    assert end_marker("catalog", style="yaml") == "# kickstart:end catalog"


def test_fence_wraps_content_and_normalizes_trailing_newline() -> None:
    fenced = fence("agent-map", "# Agent Map\n\nbody")

    assert fenced == (
        "<!-- kickstart:begin agent-map -->\n"
        "# Agent Map\n\nbody\n"
        "<!-- kickstart:end agent-map -->\n"
    )


def test_fence_round_trips_through_find() -> None:
    body = "# Title\n\ncontent line\n"
    fenced = fence("agent-map", body)

    region = find_fenced_region(fenced, "agent-map")

    assert region is not None
    assert region.inner == body


def test_fence_rejects_nested_marker_lines() -> None:
    with pytest.raises(MarkerError):
        fence("outer", "text\n<!-- kickstart:begin inner -->\ntext\n")
    with pytest.raises(MarkerError):
        fence("outer", "text\n  # kickstart:end inner\n")


def test_fence_allows_prose_mentions_of_marker_syntax() -> None:
    body = "Fenced regions use `<!-- kickstart:begin <id> -->` markers; do not edit inside them.\n"

    fenced = fence("agent-map", body)
    region = find_fenced_region(fenced, "agent-map")

    assert region is not None
    assert region.inner == body


def test_find_tolerates_crlf_line_endings() -> None:
    fenced = fence("agent-map", "body line\n").replace("\n", "\r\n")

    region = find_fenced_region(fenced, "agent-map")

    assert region is not None
    assert region.inner == "body line\r\n"


def test_invalid_artifact_id_is_rejected() -> None:
    for bad in ("Agent Map", "UPPER", "-leading", "a b", "id -->\n<!--"):
        with pytest.raises(MarkerError):
            begin_marker(bad)


def test_find_returns_none_for_premarker_text() -> None:
    assert find_fenced_region("# Plain file\n\nno markers here\n", "agent-map") is None


def test_find_fails_closed_on_malformed_markers() -> None:
    begin = begin_marker("agent-map")
    end = end_marker("agent-map")

    unpaired = f"{begin}\nbody\n"
    reversed_order = f"{end}\nbody\n{begin}\n"
    duplicated = f"{begin}\nbody\n{begin}\nbody\n{end}\n"
    foreign_nested = f"{begin}\nbody\n{begin_marker('other-id')}\n{end}\n"

    for text in (unpaired, reversed_order, duplicated, foreign_nested):
        with pytest.raises(MarkerError):
            find_fenced_region(text, "agent-map")


def test_find_ignores_midline_marker_mentions() -> None:
    mid_line = f"prose mentioning {begin_marker('agent-map')} inline\n"

    assert find_fenced_region(mid_line, "agent-map") is None


def test_find_rejects_marker_like_lines_anywhere() -> None:
    valid = fence("agent-map", "body\n")
    stray_after = valid + "user prose\n# kickstart:begin stray\n"
    trailing_prose = f"{begin_marker('agent-map')} with trailing prose\n"
    invalid_id = valid + "<!-- kickstart:begin Not_An_Id -->\n"
    indented = valid + f"    {begin_marker('other')}\n"

    for text in (stray_after, trailing_prose, invalid_id, indented):
        with pytest.raises(MarkerError):
            find_fenced_region(text, "agent-map")
    # The same globally-malformed file must also refuse replacement.
    with pytest.raises(MarkerError):
        replace_fenced_region(stray_after, "agent-map", "new body\n")


def test_find_supports_multiple_disjoint_regions() -> None:
    text = fence("agent-map", "first body\n") + "user prose between\n" + fence("catalog", "second body\n")

    first = find_fenced_region(text, "agent-map")
    second = find_fenced_region(text, "catalog")

    assert first is not None and first.inner == "first body\n"
    assert second is not None and second.inner == "second body\n"

    replaced = replace_fenced_region(text, "agent-map", "updated body\n")
    still_second = find_fenced_region(replaced, "catalog")
    assert still_second is not None and still_second.inner == "second body\n"


def test_find_accepts_marker_as_final_unterminated_line() -> None:
    text = f"{begin_marker('agent-map')}\nbody\n{end_marker('agent-map')}"

    region = find_fenced_region(text, "agent-map")

    assert region is not None
    assert region.inner == "body\n"


def test_replace_touches_only_the_owned_region() -> None:
    user_above = "user prose above\n\n"
    user_below = "\nuser prose below\n"
    text = user_above + fence("agent-map", "old body\n") + user_below

    replaced = replace_fenced_region(text, "agent-map", "new body\n")

    assert replaced == user_above + fence("agent-map", "new body\n") + user_below


def test_replace_requires_an_existing_fence() -> None:
    with pytest.raises(MarkerError):
        replace_fenced_region("no fence here\n", "agent-map", "body\n")


def test_replace_rejects_marker_bearing_replacement() -> None:
    text = fence("agent-map", "old\n")

    with pytest.raises(MarkerError):
        replace_fenced_region(text, "agent-map", f"{begin_marker('agent-map')}\n")


def test_yaml_style_round_trip() -> None:
    fenced = fence("catalog", "kind: Component\n", style="yaml")

    region = find_fenced_region(fenced, "catalog", style="yaml")

    assert region is not None
    assert region.inner == "kind: Component\n"
    assert replace_fenced_region(fenced, "catalog", "kind: System\n", style="yaml") == fence(
        "catalog", "kind: System\n", style="yaml"
    )
