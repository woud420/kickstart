from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import graph_evidence  # noqa: E402


class GraphEvidenceTests(unittest.TestCase):
    def test_projection_metrics_keeps_cycle_evidence_separate(self) -> None:
        nodes = {"src/a.py", "src/b.py", "tests/test_a.py"}
        edges = [
            {"source": "src/a.py", "target": "src/b.py", "kind": "CALLS"},
            {"source": "src/b.py", "target": "src/a.py", "kind": "CALLS"},
            {"source": "tests/test_a.py", "target": "src/a.py", "kind": "TESTED_BY"},
        ]
        metrics = graph_evidence.projection_metrics(
            nodes,
            edges,
            {"CALLS"},
            [
                {"name": "a", "prefixes": ["src/a.py"]},
                {"name": "b", "prefixes": ["src/b.py"]},
            ],
        )
        self.assertEqual(metrics["largest_scc_nodes"], 2)
        self.assertEqual(metrics["cycle_mass"], 2)
        self.assertEqual(metrics["cross_boundary_cyclic_edge_count"], 2)
        self.assertEqual(metrics["edge_count"], 2)

    def test_ambiguous_entities_are_not_resolved_arbitrarily(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary).resolve()
            graph = {
                "nodes": [
                    {
                        "kind": "Function",
                        "qualified_name": "shared",
                        "file_path": str(checkout / "src/a.py"),
                    },
                    {
                        "kind": "Function",
                        "qualified_name": "shared",
                        "file_path": str(checkout / "src/b.py"),
                    },
                    {
                        "kind": "File",
                        "qualified_name": str(checkout / "src/c.py"),
                        "name": str(checkout / "src/c.py"),
                        "file_path": str(checkout / "src/c.py"),
                    },
                ],
                "edges": [
                    {
                        "kind": "CALLS",
                        "source": str(checkout / "src/c.py"),
                        "target": "shared",
                    }
                ],
            }
            parsed, edges, mapping = graph_evidence.map_graph(graph, checkout, {"src/a.py", "src/b.py", "src/c.py"})
        self.assertEqual(parsed, {"src/c.py"})
        self.assertEqual(edges, [])
        self.assertEqual(mapping["ambiguous_entity_count"], 1)
        self.assertEqual(mapping["unresolved_edges_by_kind"], {"CALLS": 1})

    def test_export_clock_fields_do_not_change_structured_evidence(self) -> None:
        first = graph_evidence.stable_export_stats({"nodes": 4, "last_updated": "one", "generated_at": "first"})
        second = graph_evidence.stable_export_stats({"nodes": 4, "last_updated": "two", "generated_at": "second"})
        self.assertEqual(first, {"nodes": 4})
        self.assertEqual(first, second)

    def test_parser_languages_count_only_declared_source_like_files(self) -> None:
        corpus = {
            "files": [
                {"path": "src/app.py", "bytes": 10, "suffix": ".py", "source_like": True},
                {
                    "path": "pyproject.toml",
                    "bytes": 5,
                    "suffix": ".toml",
                    "source_like": False,
                },
            ]
        }
        result = graph_evidence.parser_coverage(
            corpus,
            {"src/app.py", "pyproject.toml"},
            {"src/app.py": "python", "pyproject.toml": "hcl"},
        )
        self.assertEqual(result["parsed_files"], 1)
        self.assertEqual(result["parser_languages"], {"python": 1})

    def test_crg_environment_is_allowlisted_and_network_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            Path(temporary, "sitecustomize.py").write_text(
                "raise RuntimeError('target checkout was imported')\n", encoding="utf-8"
            )
            Path(temporary, "socket.py").write_text(
                "raise RuntimeError('target checkout shadowed stdlib')\n", encoding="utf-8"
            )
            original = os.environ.get("OPENAI_API_KEY")
            os.environ["OPENAI_API_KEY"] = "must-not-cross-boundary"
            try:
                environment = graph_evidence.strict_crg_environment(Path(temporary) / "analysis" / "crg")
                network_guard = (Path(environment["PYTHONPATH"]) / "sitecustomize.py").read_text(encoding="utf-8")
                graph_evidence.verify_crg_sandbox(environment, Path(temporary))
                pycache_entries = list(Path(environment["PYTHONPYCACHEPREFIX"]).rglob("*"))
            finally:
                if original is None:
                    os.environ.pop("OPENAI_API_KEY", None)
                else:
                    os.environ["OPENAI_API_KEY"] = original
        expected = set(graph_evidence.CRG_FIXED_ENVIRONMENT) | {
            "CRG_DATA_DIR",
            "HOME",
            "MPLCONFIGDIR",
            "PATH",
            "PYTHONPATH",
            "PYTHONPYCACHEPREFIX",
            "TMPDIR",
            "XDG_CACHE_HOME",
            "XDG_CONFIG_HOME",
            "XDG_DATA_HOME",
        }
        self.assertEqual(set(environment), expected)
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertEqual(environment["GIT_ALLOW_PROTOCOL"], "file")
        self.assertEqual(environment["CRG_LEIDEN_SEED"], "42")
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(environment["TZ"], "UTC")
        self.assertEqual(
            graph_evidence.normalized_crg_environment()["PYTHONPYCACHEPREFIX"],
            "<scratch>/pycache",
        )
        self.assertEqual(network_guard, graph_evidence.NETWORK_GUARD_SOURCE)
        self.assertEqual(pycache_entries, [])

    def test_analyzer_identity_verifies_installed_files_against_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "code-review-graph"
            executable.write_text(f"#!{Path(sys.executable).resolve()}\n", encoding="utf-8")
            package_file = root / "code_review_graph" / "cli.py"
            package_file.parent.mkdir()
            package_file.write_bytes(b"trusted analyzer bytes\n")
            record_value = (
                base64.urlsafe_b64encode(hashlib.sha256(package_file.read_bytes()).digest()).decode("ascii").rstrip("=")
            )

            class PackagePath:
                hash = types.SimpleNamespace(mode="sha256", value=record_value)

                def __str__(self) -> str:
                    return "code_review_graph/cli.py"

            distribution = types.SimpleNamespace(
                files=[PackagePath()],
                locate_file=lambda _path: package_file,
                metadata={"Name": "code-review-graph"},
                version="2.3.8",
                entry_points=[
                    types.SimpleNamespace(
                        group="console_scripts",
                        name="code-review-graph",
                        value="code_review_graph.cli:main",
                    )
                ],
            )
            with mock.patch.object(graph_evidence.importlib.metadata, "distribution", return_value=distribution):
                identity = graph_evidence.measure_analyzer_identity(executable)
                self.assertEqual(identity["measured_file_count"], 1)
                package_file.write_bytes(b"tampered analyzer bytes\n")
                with self.assertRaises(graph_evidence.EvidenceError):
                    graph_evidence.measure_analyzer_identity(executable)

    def test_configuration_change_refuses_comparison(self) -> None:
        projection = graph_evidence.projection_metrics({"a"}, [], set(), [])
        digests = {name: "same" for name in graph_evidence.COMPARABILITY_DIGESTS}
        base = {
            "schema_version": graph_evidence.GRAPH_SCHEMA,
            "digests": digests,
            "repository": {"revision": "a" * 40, "slug": "owner/repo"},
            "parser": {"file_coverage": 1.0},
            "topology": {"projections": {"all": projection}},
        }
        head = json.loads(json.dumps(base))
        head["repository"]["revision"] = "b" * 40
        result = graph_evidence.compare_snapshots(
            base,
            head,
            [".github/scripts/publisher_guard.py"],
            [".github/graph-metrics.yml"],
            {},
        )
        self.assertEqual(result["comparison"]["status"], "not_comparable")
        self.assertEqual(result["comparison"]["reason"], "not comparable; rebaseline required")
        self.assertEqual(result["topology"]["status"], "not_comparable")

    def test_policy_digest_binds_behavior_fields_outside_harness(self) -> None:
        graph_policy = {"schema_version": graph_evidence.GRAPH_SCHEMA}
        first = {"harness": {"seed": 6149}, "change_intent": "preserve"}
        second = {"harness": {"seed": 6149}, "change_intent": "extend"}
        self.assertNotEqual(
            graph_evidence.evidence_policy_digest(graph_policy, first),
            graph_evidence.evidence_policy_digest(graph_policy, second),
        )

    def test_structured_digest_ignores_only_contract_fields(self) -> None:
        first = {"value": 1, "generated_at": "one"}
        first["artifact_digest"] = graph_evidence.structured_digest(first)
        second = {"value": 1, "generated_at": "two", "artifact_digest": "ignored"}
        self.assertEqual(first["artifact_digest"], graph_evidence.structured_digest(second))
        second["value"] = 2
        self.assertNotEqual(first["artifact_digest"], graph_evidence.structured_digest(second))


if __name__ == "__main__":
    unittest.main()
