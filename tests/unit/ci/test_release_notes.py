from pathlib import Path
import re

import pytest

from ci.release_notes import changelog_summary, release_body

REPO_ROOT = Path(__file__).resolve().parents[3]
CHANGELOG = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_every_changelog_version_opens_with_a_summary() -> None:
    versions = re.findall(r"^## v(\S+)", CHANGELOG, re.MULTILINE)

    assert versions
    for version in versions:
        summary = changelog_summary(CHANGELOG, version)
        assert summary and not summary.startswith("#"), version


def test_summary_is_the_opening_paragraph_joined_onto_one_line() -> None:
    changelog = "## v1.2.3 - 2026-01-01\n\nFirst line\nsecond line.\n\nMore detail.\n\n### Fixed\n\n- x\n"

    assert changelog_summary(changelog, "1.2.3") == "First line second line."


def test_summary_requires_the_version_and_its_paragraph() -> None:
    with pytest.raises(ValueError, match="no section for v9.9.9"):
        changelog_summary(CHANGELOG, "9.9.9")
    with pytest.raises(ValueError, match="no summary paragraph"):
        changelog_summary("## v1.0.0 - 2026-01-01\n\n### Fixed\n", "1.0.0")


def test_release_body_links_the_tag_and_keeps_install_short() -> None:
    body = release_body(CHANGELOG, "v0.4.5", "woud420/kickstart")

    assert body.startswith("Self-upgrade reliability release.")
    assert "https://github.com/woud420/kickstart/blob/v0.4.5/CHANGELOG.md" in body
    assert "raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh | bash" in body
    assert "kickstart telemetry disable" in body
    assert len(body.splitlines()) < 25


def test_release_body_rejects_non_release_tags() -> None:
    with pytest.raises(ValueError, match="not a stable release tag"):
        release_body(CHANGELOG, "v0.5.0-rc.1", "woud420/kickstart")
