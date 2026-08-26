#!/usr/bin/env python3
"""Validate an untrusted evidence artifact and render safe publication text.

The trusted workflow_run publisher executes this file from the default-branch
checkout.  It treats the triggering workflow's zip as hostile data, performs
bounded manual extraction, validates identity/schema/digests, and never
publishes artifact-supplied Markdown.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import shutil
import stat
import sys
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

GRAPH_EVIDENCE_PATH = Path(__file__).resolve().with_name("graph_evidence.py")
GRAPH_EVIDENCE_SPEC = importlib.util.spec_from_file_location("trusted_graph_evidence", GRAPH_EVIDENCE_PATH)
if GRAPH_EVIDENCE_SPEC is None or GRAPH_EVIDENCE_SPEC.loader is None:
    raise RuntimeError("cannot load the trusted graph-evidence helper")
graph_evidence = importlib.util.module_from_spec(GRAPH_EVIDENCE_SPEC)
GRAPH_EVIDENCE_SPEC.loader.exec_module(graph_evidence)

PUBLISHER_VERSION = "1.0.0"
SCRIPT = Path(__file__).resolve()
ALLOWED_FILES = {
    "manifest.json",
    "snapshot.json",
    "comparison.json",
    "history.ndjson",
    "behavior-evidence.json",
    "delphi-rounds.json",
    "report.md",
}
JSON_LIMIT = 8 * 1024 * 1024
HISTORY_LIMIT = 25 * 1024 * 1024
MANIFEST_LIMIT = 128 * 1024
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SAFE_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class PublicationError(RuntimeError):
    """The artifact is unsafe, malformed, or not bound to the triggering run."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicationError(f"cannot parse {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise PublicationError(f"{path.name} must contain a JSON object")
    return value


def exact_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PublicationError(f"{label} must be a non-negative integer")
    return int(value)


def clean(value: Any, limit: int = 240) -> str:
    text = CONTROL_RE.sub("", str(value))
    text = "".join(character for character in text if unicodedata.category(character) != "Cf")
    for source, replacement in (
        ("\\", "＼"),
        ("`", "｀"),
        ("*", "＊"),
        ("[", "［"),
        ("]", "］"),
        ("(", "（"),
        (")", "）"),
        ("#", "＃"),
        ("!", "！"),
        ("@", "＠"),
    ):
        text = text.replace(source, replacement)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    return text[:limit] + ("…" if len(text) > limit else "")


def finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PublicationError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or abs(result) > 1_000_000_000:
        raise PublicationError(f"{label} is outside the accepted range")
    return result


def validate_archive(archive: Path, destination: Path, policy: Mapping[str, Any]) -> None:
    publication = policy.get("publication", {})
    max_compressed = exact_int(publication.get("artifact_max_compressed_bytes"), "artifact_max_compressed_bytes")
    max_uncompressed = exact_int(publication.get("artifact_max_uncompressed_bytes"), "artifact_max_uncompressed_bytes")
    if not archive.is_file() or archive.is_symlink():
        raise PublicationError("downloaded artifact must be one regular zip file")
    if archive.stat().st_size <= 0 or archive.stat().st_size > max_compressed:
        raise PublicationError("artifact compressed size is outside policy")
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    try:
        bundle = zipfile.ZipFile(archive)
    except (OSError, zipfile.BadZipFile) as exc:
        raise PublicationError(f"artifact is not a valid zip: {exc}") from exc
    with bundle:
        infos = bundle.infolist()
        if len(infos) != len(ALLOWED_FILES):
            raise PublicationError("artifact entry count does not match the publication contract")
        names = [info.filename for info in infos]
        if set(names) != ALLOWED_FILES or len(names) != len(set(names)):
            raise PublicationError("artifact contains missing, duplicate, or unexpected paths")
        total = 0
        for info in infos:
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename or "\x00" in info.filename:
                raise PublicationError(f"unsafe artifact path: {info.filename!r}")
            mode = info.external_attr >> 16
            file_type = stat.S_IFMT(mode)
            if file_type not in (0, stat.S_IFREG):
                raise PublicationError(f"artifact entry is not a regular file: {info.filename}")
            limit = MANIFEST_LIMIT if info.filename == "manifest.json" else JSON_LIMIT
            if info.filename == "history.ndjson":
                limit = HISTORY_LIMIT
            elif info.filename == "report.md":
                limit = exact_int(publication.get("markdown_max_bytes"), "markdown_max_bytes")
            if info.file_size < 0 or info.file_size > limit:
                raise PublicationError(f"artifact entry exceeds its size limit: {info.filename}")
            if info.compress_size == 0 and info.file_size != 0:
                raise PublicationError(f"invalid compression metadata for {info.filename}")
            if info.compress_size and info.file_size / info.compress_size > 200:
                raise PublicationError(f"artifact entry compression ratio is excessive: {info.filename}")
            total += info.file_size
            if total > max_uncompressed:
                raise PublicationError("artifact uncompressed size exceeds policy")
        for info in infos:
            target = destination / info.filename
            remaining = info.file_size
            with bundle.open(info, "r") as source, target.open("wb") as output:
                while remaining:
                    chunk = source.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise PublicationError(f"truncated artifact entry: {info.filename}")
                    output.write(chunk)
                    remaining -= len(chunk)
                if source.read(1):
                    raise PublicationError(f"artifact entry exceeded declared size: {info.filename}")


def verify_structured(path: Path, schema: str, artifact_type: str) -> dict[str, Any]:
    value = load_json(path)
    if value.get("schema_version") != schema or value.get("artifact_type") != artifact_type:
        raise PublicationError(f"{path.name} has an unsupported schema or artifact type")
    if value.get("artifact_digest") != graph_evidence.structured_digest(value):
        raise PublicationError(f"{path.name} structured digest mismatch")
    return value


def verify_history(path: Path) -> None:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PublicationError(f"history.ndjson:{number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict) or value.get("schema_version") != "graph-history/1.0.0":
            raise PublicationError(f"history.ndjson:{number}: unsupported record")
        if value.get("artifact_digest") != graph_evidence.structured_digest(value):
            raise PublicationError(f"history.ndjson:{number}: digest mismatch")


def expected_digests(
    policy: Mapping[str, Any],
    behavior_policy: Mapping[str, Any],
    lock_path: Path,
) -> dict[str, str]:
    analyzer_identity = {
        "distribution_name": str(policy["analyzer"]["name"]),
        "cli_version": f"code-review-graph {policy['analyzer']['version']}",
        "version": str(policy["analyzer"]["version"]),
        "installed_code_sha256": str(policy["analyzer"]["installed_code_sha256"]),
    }
    return {
        "analyzer": str(policy["analyzer"]["installed_code_sha256"]),
        "analyzer_distribution": str(policy["analyzer"]["distribution_sha256"]),
        "dependency_lock": graph_evidence.digest_file(lock_path),
        "policy": graph_evidence.evidence_policy_digest(policy, behavior_policy),
        "corpus": graph_evidence.digest_bytes(graph_evidence.canonical_bytes(policy.get("corpus", {}))),
        "normalizer": graph_evidence.digest_bytes(
            graph_evidence.canonical_bytes(
                {
                    "version": graph_evidence.NORMALIZER_VERSION,
                    "contract": graph_evidence.NORMALIZER_CONTRACT,
                }
            )
        ),
        "harness": graph_evidence.digest_bytes(graph_evidence.canonical_bytes(behavior_policy.get("harness", {}))),
        "evaluator": graph_evidence.digest_file(GRAPH_EVIDENCE_PATH),
        "environment": graph_evidence.digest_bytes(
            graph_evidence.canonical_bytes(graph_evidence.environment_manifest(analyzer_identity))
        ),
        "runtime": graph_evidence.digest_bytes(graph_evidence.canonical_bytes(graph_evidence.measured_runtime())),
        "sandbox": graph_evidence.sandbox_digest(),
    }


def verify_evidence_digests(
    manifest: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    comparison: Mapping[str, Any],
    behavior: Mapping[str, Any],
) -> Mapping[str, Any]:
    actual = manifest.get("digests")
    if not isinstance(actual, dict):
        raise PublicationError("manifest digest inventory is invalid")
    for name in graph_evidence.COMPARABILITY_DIGESTS:
        value = actual.get(name)
        if not isinstance(value, str) or not SAFE_DIGEST_RE.fullmatch(value):
            raise PublicationError(f"manifest comparability digest is invalid: {name}")
    if snapshot.get("digests") != actual or comparison.get("digests") != actual:
        raise PublicationError("snapshot/comparison digest inventory does not match manifest")
    behavior_digests = behavior.get("digests", {})
    for name in ("dependency_lock", "environment", "harness"):
        if behavior_digests.get(name) != actual.get(name):
            raise PublicationError(f"behavior digest does not match graph evidence: {name}")
    return actual


def verify_identity(
    manifest: Mapping[str, Any],
    metadata: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    comparison: Mapping[str, Any],
    behavior: Mapping[str, Any],
    delphi: Mapping[str, Any],
) -> None:
    workflow = manifest.get("workflow", {})
    revision = manifest.get("revision", {})
    required_pairs = {
        "repository": (workflow.get("repository"), metadata.get("repository")),
        "repository_id": (workflow.get("repository_id"), metadata.get("repository_id")),
        "run_id": (workflow.get("run_id"), metadata.get("run_id")),
        "run_attempt": (workflow.get("run_attempt"), metadata.get("run_attempt")),
        "event_name": (workflow.get("event_name"), metadata.get("event_name")),
        "head_sha": (revision.get("head_sha"), metadata.get("head_sha")),
        "head_repository_id": (
            revision.get("head_repository_id"),
            metadata.get("head_repository_id"),
        ),
    }
    for label, (actual, expected) in required_pairs.items():
        if actual != expected:
            raise PublicationError(f"manifest {label} does not match the trusted workflow run")
    if metadata.get("event_name") == "pull_request":
        if revision.get("pr_number") != metadata.get("pr_number"):
            raise PublicationError("manifest PR number does not match the verified PR")
        if revision.get("base_sha") != metadata.get("base_sha"):
            raise PublicationError("manifest base SHA does not match the verified PR")
    if comparison.get("repository", {}).get("base_revision") != revision.get("base_sha"):
        raise PublicationError("comparison base SHA does not match manifest")
    if comparison.get("repository", {}).get("head_revision") != revision.get("head_sha"):
        raise PublicationError("comparison head SHA does not match manifest")
    if snapshot.get("repository", {}).get("revision") != revision.get("head_sha"):
        raise PublicationError("snapshot head SHA does not match manifest")
    if snapshot.get("repository", {}).get("slug") != metadata.get("repository"):
        raise PublicationError("snapshot repository does not match the trusted workflow run")
    for label, evidence in (("behavior", behavior), ("Delphi", delphi)):
        evidence_repository = evidence.get("repository", {})
        if evidence_repository.get("base_revision") != revision.get("base_sha") or evidence_repository.get(
            "head_revision"
        ) != revision.get("head_sha"):
            raise PublicationError(f"{label} revisions do not match manifest")
    if manifest.get("comparability") != comparison.get("comparison"):
        raise PublicationError("manifest comparability decision does not match comparison")
    graph_evidence.validate_sha(str(revision.get("base_sha", "")), "manifest base SHA")
    graph_evidence.validate_sha(str(revision.get("head_sha", "")), "manifest head SHA")


def verify_manifest_files(root: Path, manifest: Mapping[str, Any]) -> None:
    records = manifest.get("files")
    if not isinstance(records, list) or len(records) != len(ALLOWED_FILES) - 1:
        raise PublicationError("manifest file inventory is invalid")
    expected = ALLOWED_FILES - {"manifest.json"}
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise PublicationError("manifest file record must be an object")
        name = record.get("path")
        if name not in expected or name in seen:
            raise PublicationError("manifest file inventory contains an unexpected path")
        seen.add(str(name))
        path = root / str(name)
        if path.stat().st_size != exact_int(record.get("size"), f"size for {name}"):
            raise PublicationError(f"size mismatch for {name}")
        digest = record.get("sha256")
        if not isinstance(digest, str) or not SAFE_DIGEST_RE.fullmatch(digest):
            raise PublicationError(f"invalid digest for {name}")
        if graph_evidence.digest_file(path) != digest:
            raise PublicationError(f"digest mismatch for {name}")
    if seen != expected:
        raise PublicationError("manifest file inventory is incomplete")


def render_safe(
    policy: Mapping[str, Any],
    metadata: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    comparison: Mapping[str, Any],
    behavior: Mapping[str, Any],
    delphi: Mapping[str, Any],
    force_noncomparable: bool,
) -> str:
    marker = str(policy.get("publication", {}).get("sticky_comment_marker", ""))
    if marker != "<!-- kickstart-architecture-evidence-v1 -->":
        raise PublicationError("trusted sticky-comment marker is not the expected constant")
    repository = str(metadata.get("repository", ""))
    if not REPOSITORY_RE.fullmatch(repository):
        raise PublicationError("invalid repository identity")
    head_sha = graph_evidence.validate_sha(str(metadata.get("head_sha", "")), "head SHA")
    run_id = exact_int(metadata.get("run_id"), "run_id")
    decision = comparison.get("comparison", {})
    status = str(decision.get("status", "not_comparable"))
    reason = str(decision.get("reason", "not comparable; rebaseline required"))
    if force_noncomparable:
        status = "not_comparable"
        reason = "not comparable; rebaseline required"
    lines = [
        marker,
        "## Architecture and behavioral evidence",
        "",
        "> Report-only pilot. Machine topology, behavioral evidence, and Delphi-inspired judgment remain separate; no composite quality score is calculated.",
        "",
        f"Comparability: **{clean(status)}** — {clean(reason)}",
        "",
    ]
    if force_noncomparable:
        lines += [
            "Evaluator, workflow, policy, or dependency-lock files changed in this pull request. Metrics are intentionally withheld until a trusted rebaseline.",
            "",
        ]
    else:
        parser = snapshot.get("parser", {})
        file_coverage = finite_number(parser.get("file_coverage", 0), "file coverage")
        lines += [
            "### Machine signal",
            "",
            f"- Parser coverage: {100 * file_coverage:.1f}% ({exact_int(parser.get('parsed_files'), 'parsed files')} / {exact_int(parser.get('source_like_files'), 'source-like files')} files)",
            f"- Unsupported source-like files: {exact_int(parser.get('unsupported_count'), 'unsupported files')}",
        ]
        synchronous = snapshot.get("topology", {}).get("projections", {}).get("synchronous", {})
        for label, key in (
            ("Largest synchronous SCC", "largest_scc_nodes"),
            ("Synchronous cycle mass", "cycle_mass"),
            ("Cross-boundary cyclic edges", "cross_boundary_cyclic_edge_count"),
        ):
            lines.append(f"- {label}: {finite_number(synchronous.get(key, 0), key):g}")
        risk = comparison.get("crg", {}).get("risk", {})
        risk_level = risk.get("risk_level")
        risk_score = risk.get("risk_score")
        digests = snapshot.get("digests", {})
        lines += [
            f"- CRG heuristic risk level: `{clean(risk_level if risk_level is not None else 'not reported')}`",
            f"- CRG heuristic risk score: `{clean(risk_score if risk_score is not None else 'not reported')}`",
            f"- Analyzer installed-code digest: `{clean(digests.get('analyzer', 'not reported'))}`",
            f"- Analyzer distribution digest: `{clean(digests.get('analyzer_distribution', 'not reported'))}`",
            f"- Policy digest: `{clean(digests.get('policy', 'not reported'))}`",
            f"- Evaluator digest: `{clean(digests.get('evaluator', 'not reported'))}`",
            f"- Sandbox digest: `{clean(digests.get('sandbox', 'not reported'))}`",
            "",
        ]
    if force_noncomparable:
        lines += [
            "### Behavioral evidence",
            "",
            "- Withheld because the evidence configuration or evaluator changed; no trusted behavioral conclusion is published.",
            "",
            "### Delphi-inspired judgment",
            "",
            "- Withheld because the evidence configuration or evaluator changed; no trusted panel conclusion is published.",
            "",
        ]
    else:
        lane = behavior.get("behavior", {})
        lines += [
            "### Behavioral evidence",
            "",
            f"- Change intent: `{clean(lane.get('change_intent', 'unknown'))}`",
            f"- Result: `{clean(lane.get('evidence_result', 'inconclusive'))}`",
            f"- Status: `{clean(lane.get('status', 'not_collected'))}`",
            f"- Unmeasured surfaces: {len(lane.get('unmeasured_surfaces', [])) if isinstance(lane.get('unmeasured_surfaces'), list) else 0}",
            "",
            "### Delphi-inspired judgment",
            "",
            f"- Panel: {clean(delphi.get('panel', {}).get('label', 'Delphi-inspired correlated agent panel'))}",
            f"- Locked rounds: {len(delphi.get('rounds', [])) if isinstance(delphi.get('rounds'), list) else 0}",
            "- Same-family agreement would measure correlated repeatability, not independent expert confidence.",
            "",
        ]
    lines += [
        f"[Analyzed commit](https://github.com/{repository}/commit/{head_sha}) · [Workflow run](https://github.com/{repository}/actions/runs/{run_id})",
        "",
        "Architecture evidence prioritizes investigation only. It does not prove behavior, gate this pull request, or authorize a refactor.",
        "",
    ]
    rendered = "\n".join(lines)
    max_bytes = exact_int(policy.get("publication", {}).get("markdown_max_bytes"), "markdown_max_bytes")
    if len(rendered.encode("utf-8")) > max_bytes:
        raise PublicationError("sanitized Markdown exceeds policy")
    return rendered


def validate_command(args: argparse.Namespace) -> int:
    policy_path = Path(args.policy).resolve()
    behavior_policy_path = Path(args.behavior_policy).resolve()
    lock_path = Path(args.dependency_lock).resolve()
    metadata = load_json(Path(args.metadata).resolve())
    policy = load_json(policy_path)
    behavior_policy = load_json(behavior_policy_path)
    if metadata.get("schema_version") != "architecture-evidence-workflow-run/1.0.0":
        raise PublicationError("trusted workflow-run metadata schema is unsupported")
    if not isinstance(metadata.get("configuration_changed"), bool):
        raise PublicationError("trusted configuration-change decision is invalid")
    if policy.get("schema_version") != graph_evidence.GRAPH_SCHEMA:
        raise PublicationError("trusted graph policy schema is unsupported")
    if behavior_policy.get("schema_version") != "behavior-policy/1.0.0":
        raise PublicationError("trusted behavior policy schema is unsupported")
    destination = Path(args.output).resolve()
    extracted = destination / "extracted"
    validate_archive(Path(args.archive).resolve(), extracted, policy)
    manifest = verify_structured(
        extracted / "manifest.json",
        str(policy.get("publication", {}).get("artifact_schema")),
        "architecture-evidence-publication",
    )
    snapshot = verify_structured(extracted / "snapshot.json", graph_evidence.GRAPH_SCHEMA, "snapshot")
    comparison = verify_structured(extracted / "comparison.json", graph_evidence.GRAPH_SCHEMA, "comparison")
    behavior = verify_structured(
        extracted / "behavior-evidence.json", graph_evidence.BEHAVIOR_SCHEMA, "behavior-evidence"
    )
    delphi = verify_structured(extracted / "delphi-rounds.json", graph_evidence.DELPHI_SCHEMA, "delphi-rounds")
    verify_history(extracted / "history.ndjson")
    verify_manifest_files(extracted, manifest)
    verify_identity(manifest, metadata, snapshot, comparison, behavior, delphi)
    configuration_changed = bool(metadata.get("configuration_changed"))
    expected = expected_digests(policy, behavior_policy, lock_path)
    actual = verify_evidence_digests(manifest, snapshot, comparison, behavior)
    mismatched = sorted(name for name, value in expected.items() if actual.get(name) != value)
    if mismatched and not configuration_changed:
        raise PublicationError(f"unexpected trusted evaluator digest mismatch: {mismatched}")
    if configuration_changed and comparison.get("comparison", {}).get("status") != "not_comparable":
        raise PublicationError("configuration-changing PR did not mark comparison non-comparable")
    if comparison.get("comparison", {}).get("configuration_changed") != configuration_changed:
        raise PublicationError("configuration-change decisions do not match")
    destination.mkdir(parents=True, exist_ok=True)
    body = render_safe(
        policy,
        metadata,
        snapshot,
        comparison,
        behavior,
        delphi,
        configuration_changed or bool(mismatched),
    )
    (destination / "comment.md").write_text(body, encoding="utf-8")
    publication_metadata = {
        "schema_version": "architecture-evidence-publication/1.0.0",
        "publisher": {
            "name": SCRIPT.name,
            "version": PUBLISHER_VERSION,
            "digest": graph_evidence.digest_file(SCRIPT),
        },
        "repository": metadata.get("repository"),
        "repository_id": metadata.get("repository_id"),
        "source_run_id": metadata.get("run_id"),
        "source_run_attempt": metadata.get("run_attempt"),
        "event_name": metadata.get("event_name"),
        "pr_number": metadata.get("pr_number"),
        "head_sha": metadata.get("head_sha"),
        "comment_sha256": graph_evidence.digest_file(destination / "comment.md"),
    }
    (destination / "publication-metadata.json").write_bytes(graph_evidence.canonical_bytes(publication_metadata))
    shutil.rmtree(extracted)
    print(destination / "comment.md")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--archive", required=True)
    validate.add_argument("--metadata", required=True)
    validate.add_argument("--policy", required=True)
    validate.add_argument("--behavior-policy", required=True)
    validate.add_argument("--dependency-lock", required=True)
    validate.add_argument("--output", required=True)
    validate.set_defaults(func=validate_command)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return int(args.func(args))
    except (PublicationError, graph_evidence.EvidenceError, OSError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
