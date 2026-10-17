"""Generate the closed schema-4 shape from TypedDicts and validate its invariants."""

import json
from typing import Literal, NotRequired, Required, cast, get_args, get_origin, get_type_hints, is_typeddict

from jsonschema import Draft202012Validator
from src.generator.managed_artifacts import ALL_MANAGED_DOCS, OWNERSHIP_PATH_PATTERN, WORKFLOW_PATTERN
from src.generator.manifest_types import JsonValue, ParsedManifest, ScaffoldManifestV4, SystemScaffoldManifest
from src.utils.errors import ManifestShapeError


def _shape(annotation: type) -> ParsedManifest:
    origin = get_origin(annotation)
    if origin in (NotRequired, Required):
        return _shape(get_args(annotation)[0])
    if annotation is str:
        return {"type": "string", "minLength": 1}
    if origin is Literal:
        return {"enum": list(get_args(annotation))}
    if origin is list:
        return {"type": "array", "items": _shape(get_args(annotation)[0])}
    if origin is dict:
        return {"type": "object", "additionalProperties": _shape(get_args(annotation)[1])}
    if is_typeddict(annotation):
        hints = get_type_hints(annotation, include_extras=True)
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [key for key in sorted(cast(frozenset[str], getattr(annotation, "__required_keys__")))],
            "properties": {name: _shape(hint) for name, hint in hints.items()},
        }
    raise TypeError(f"unsupported schema annotation: {annotation!r}")


def _at(path: str, rule: ParsedManifest) -> ParsedManifest:
    for part in reversed(path.split(".")):
        rule = {"properties": {part: rule}, "required": [part]}
    return rule


def _when(condition: ParsedManifest, consequence: ParsedManifest) -> ParsedManifest:
    return {"if": condition, "then": consequence}


def manifest_v4_schema() -> ParsedManifest:
    """Return the portable structural schema plus supported identity invariants."""
    schema = _shape(ScaffoldManifestV4)
    rules: list[JsonValue] = [
        _when(
            _at("project.kind", {"const": "system"}),
            {
                "required": ["composition"],
                "properties": {
                    "project": {
                        "not": {
                            "anyOf": [
                                {"required": ["language"]},
                                {"required": ["framework"]},
                            ]
                        }
                    }
                },
            },
        ),
        _when(
            {"not": _at("project.kind", {"const": "system"})},
            {
                "not": {"required": ["composition"]},
                "properties": {"project": {"required": ["language"]}},
            },
        ),
    ]
    languages = {
        "service": ["python", "rust", "typescript", "go", "cpp"],
        "library": ["python", "rust"],
        "cli": ["python", "rust", "typescript"],
        "frontend": ["typescript"],
    }
    for kind, allowed in languages.items():
        rules.append(
            _when(_at("project.kind", {"const": kind}), _at("project.language", {"enum": [value for value in allowed]}))
        )
    for kind, model in {"cli": "cli", "library": "library", "frontend": "static-site"}.items():
        rules.append(_when(_at("project.kind", {"const": kind}), _at("execution.models", {"const": [model]})))
    rules.append(
        _when(
            _at("project.kind", {"const": "service"}),
            _at("execution.models", {"enum": [["container"], ["cloudflare-worker"]]}),
        )
    )
    rules.append(
        _when(
            _at("project.kind", {"const": "system"}),
            _at("execution.models", {"items": {"enum": ["container", "cloudflare-worker"]}, "uniqueItems": True}),
        )
    )
    worker: ParsedManifest = {
        "allOf": [
            _at("project.kind", {"const": "service"}),
            _at("execution.models", {"contains": {"const": "cloudflare-worker"}}),
        ]
    }
    rules.append(
        _when(
            worker,
            {
                "allOf": [
                    _at("project.kind", {"const": "service"}),
                    _at("project.language", {"enum": ["typescript", "rust"]}),
                    _at("execution.models", {"const": ["cloudflare-worker"]}),
                    _at("execution.platforms", {"const": ["cloudflare-workers"]}),
                    _at("provider.targets", {"contains": {"const": "cloudflare"}}),
                    _at("artifacts.worker", {"const": "wrangler"}),
                ]
            },
        )
    )
    for language, framework in (("python", "typer"), ("rust", "clap"), ("typescript", "oclif")):
        rules.append(
            _when(
                {
                    "allOf": [
                        _at("project.kind", {"const": "cli"}),
                        _at("project.language", {"const": language}),
                    ]
                },
                {
                    "allOf": [
                        _at("project.framework", {"const": framework}),
                        {"properties": {"project": {"properties": {"cli_framework": {"const": framework}}}}},
                    ]
                },
            )
        )
    rules.append(_when(_at("project.kind", {"const": "frontend"}), _at("project.framework", {"const": "react"})))
    rules.append(
        _when(
            {
                "allOf": [
                    _at("project.kind", {"const": "service"}),
                    _at("project.language", {"const": "python"}),
                ]
            },
            _at("project.framework", {"enum": ["fastapi", "minimal"]}),
        )
    )
    rules.append({"properties": {"ownership": _ownership_rules()}})
    schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://github.com/woud420/kickstart/blob/master/docs/contracts/scaffold-4.0.schema.json",
            "title": "Kickstart scaffold manifest 4.0",
            "allOf": rules,
        }
    )
    return schema


def validate_v4_manifest(manifest: ParsedManifest) -> None:
    """Reject unsupported fields and shapes without discarding recorded metadata."""
    errors = sorted(_V4_VALIDATOR.iter_errors(manifest), key=lambda e: (list(map(str, e.absolute_path)), e.message))
    if errors:
        error = errors[0]
        path = ".".join(map(str, error.absolute_path)) or "root"
        raise ManifestShapeError(f"manifest {path}: {error.message}")


def manifest_v4_schema_json() -> str:
    return json.dumps(manifest_v4_schema(), indent=2, sort_keys=True) + "\n"


def validate_legacy_migration_source(manifest: ParsedManifest) -> None:
    """Reject metadata a format conversion would otherwise silently discard."""
    schema = _shape(SystemScaffoldManifest)
    schema["required"] = [
        "schema_version",
        "project",
        "execution",
        "artifacts",
        "provider",
        "capabilities",
        "lifecycle",
        "knowledge_adapter",
    ]
    errors = sorted(
        Draft202012Validator(schema).iter_errors(manifest), key=lambda e: (list(map(str, e.absolute_path)), e.message)
    )
    if errors:
        error = errors[0]
        path = ".".join(map(str, error.absolute_path)) or "root"
        raise ManifestShapeError(f"manifest {path}: {error.message}")


def _ownership_rules() -> ParsedManifest:
    import re

    patterns: ParsedManifest = {
        "^" + re.escape(artifact.target) + "$": {"enum": ["seed", artifact.id]} for artifact in ALL_MANAGED_DOCS
    }
    for pattern, check in (
        (r"^Makefile$", "make-check"),
        (WORKFLOW_PATTERN, "workflow-presence"),
        (r"^\.kickstart/scaffold\.json$", "manifest-shape"),
    ):
        patterns[pattern] = {"enum": ["seed", check]}
    return {
        "propertyNames": {"allOf": [{"pattern": OWNERSHIP_PATH_PATTERN}, {"not": {"pattern": r"[\r\n]"}}]},
        "patternProperties": patterns,
        "additionalProperties": {"const": "seed"},
    }


_V4_VALIDATOR = Draft202012Validator(manifest_v4_schema())
