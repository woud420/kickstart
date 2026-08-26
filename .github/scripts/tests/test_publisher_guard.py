from __future__ import annotations

import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import publisher_guard  # noqa: E402


def policy() -> dict:
    return {
        "publication": {
            "artifact_max_compressed_bytes": 1_000_000,
            "artifact_max_uncompressed_bytes": 2_000_000,
            "markdown_max_bytes": 60_000,
            "sticky_comment_marker": "<!-- kickstart-architecture-evidence-v1 -->",
        }
    }


class PublisherGuardTests(unittest.TestCase):
    def make_archive(self, root: Path, *, extra: str | None = None, symlink: bool = False) -> Path:
        archive = root / "artifact.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for name in sorted(publisher_guard.ALLOWED_FILES):
                info = zipfile.ZipInfo(name)
                if symlink and name == "report.md":
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                else:
                    info.external_attr = (stat.S_IFREG | 0o644) << 16
                bundle.writestr(info, b"" if name == "history.ndjson" else b"{}\n")
            if extra:
                bundle.writestr(extra, b"unsafe")
        return archive

    def test_bounded_archive_is_manually_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = self.make_archive(root)
            destination = root / "out"
            publisher_guard.validate_archive(archive, destination, policy())
            self.assertEqual({path.name for path in destination.iterdir()}, publisher_guard.ALLOWED_FILES)

    def test_archive_rejects_unexpected_or_traversal_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = self.make_archive(root, extra="../escape")
            with self.assertRaises(publisher_guard.PublicationError):
                publisher_guard.validate_archive(archive, root / "out", policy())

    def test_archive_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = self.make_archive(root, symlink=True)
            with self.assertRaises(publisher_guard.PublicationError):
                publisher_guard.validate_archive(archive, root / "out", policy())

    def test_renderer_escapes_mentions_and_html(self) -> None:
        snapshot = {
            "parser": {
                "file_coverage": 0.5,
                "parsed_files": 1,
                "source_like_files": 2,
                "unsupported_count": 1,
            },
            "topology": {
                "projections": {
                    "synchronous": {
                        "largest_scc_nodes": 2,
                        "cycle_mass": 2,
                        "cross_boundary_cyclic_edge_count": 1,
                    }
                }
            },
        }
        comparison = {
            "comparison": {
                "status": "comparable",
                "reason": "<b>@team</b> [click](https://invalid.example)\u202e",
            },
            "crg": {"risk": {"risk_level": "low", "risk_score": 0.1}},
        }
        metadata = {
            "repository": "owner/repo",
            "head_sha": "a" * 40,
            "run_id": 1,
        }
        body = publisher_guard.render_safe(
            policy(),
            metadata,
            snapshot,
            comparison,
            {"behavior": {"change_intent": "preserve", "evidence_result": "inconclusive"}},
            {"panel": {"label": "Delphi-inspired correlated agent panel"}, "rounds": []},
            False,
        )
        self.assertNotIn("@team", body)
        self.assertNotIn("<b>", body)
        self.assertIn("＠team", body)
        self.assertIn("&lt;b&gt;", body)
        self.assertNotIn("\u202e", body)
        self.assertNotIn("](https://invalid.example)", body)

    def test_configuration_change_withholds_machine_metrics(self) -> None:
        body = publisher_guard.render_safe(
            policy(),
            {"repository": "owner/repo", "head_sha": "a" * 40, "run_id": 1},
            {},
            {"comparison": {"status": "comparable", "reason": "comparable"}},
            {"behavior": {"evidence_result": "forged-supported"}},
            {"panel": {"label": "forged-panel"}, "rounds": ["forged-round"]},
            True,
        )
        self.assertIn("not comparable; rebaseline required", body)
        self.assertIn("Metrics are intentionally withheld", body)
        self.assertNotIn("Parser coverage", body)
        self.assertNotIn("forged-supported", body)
        self.assertNotIn("forged-panel", body)

    def test_comparability_digests_are_bound_across_lanes(self) -> None:
        digests = {
            name: f"{index:064x}"
            for index, name in enumerate(publisher_guard.graph_evidence.COMPARABILITY_DIGESTS, start=1)
        }
        actual = publisher_guard.verify_evidence_digests(
            {"digests": digests},
            {"digests": digests},
            {"digests": digests},
            {"digests": {name: digests[name] for name in ("dependency_lock", "environment", "harness")}},
        )
        self.assertEqual(actual, digests)
        with self.assertRaises(publisher_guard.PublicationError):
            publisher_guard.verify_evidence_digests(
                {"digests": digests},
                {"digests": {**digests, "harness": "f" * 64}},
                {"digests": digests},
                {"digests": {name: digests[name] for name in ("dependency_lock", "environment", "harness")}},
            )


if __name__ == "__main__":
    unittest.main()
