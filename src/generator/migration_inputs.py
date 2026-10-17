"""Resolve only metadata that a legacy manifest actually records."""

from dataclasses import dataclass, replace
import re
from typing import cast

from src.generator.manifest_schema import validate_legacy_migration_source
from src.generator.manifest_types import ParsedManifest, ScaffoldCompositionManifest
from src.generator.scaffold_contract import ScaffoldContract
from src.stack.profile import stack_registry
from src.utils.errors import ManifestShapeError

_NATIVE = {"python": "typer", "rust": "clap", "typescript": "oclif"}
_SEMANTICS = re.compile(
    r"https://github\.com/woud420/kickstart/blob/v(\d+\.\d+\.\d+)/docs/(?:contracts/)?scaffold-contract\.md"
)
_DOCS = {
    "agent_map": "AGENTS.md",
    "architecture": "docs/architecture/",
    "contracts": "docs/contracts/",
    "operations": "docs/operations/",
    "decisions": "docs/decisions/",
}


@dataclass(frozen=True)
class MigrationDiagnostic:
    path: str
    code: str
    message: str
    blocking: bool = True


def _choice(path: str, values: list[str | None]) -> str | None:
    known = {value for value in values if value is not None}
    if len(known) > 1:
        raise ManifestShapeError(f"conflicting {path}: {', '.join(sorted(known))}")
    return next(iter(known), None)


def resolve_migration_inputs(
    source: ParsedManifest,
    language: str | None = None,
    framework: str | None = None,
) -> tuple[ScaffoldContract, tuple[MigrationDiagnostic, ...]]:
    """Resolve recorded choices and explicit overrides; never inspect app files."""
    old = ScaffoldContract.from_manifest(source)
    if old.schema_version != "4.0":
        validate_legacy_migration_source(source)
        if "docs" in source and source["docs"] != _DOCS:
            raise ManifestShapeError("nonstandard legacy docs mapping cannot be discarded; review it before migrating")
        if "composition" in source and old.project_kind != "system":
            raise ManifestShapeError("composition is only supported for system projects")
    normalize = stack_registry.normalize_language
    recorded_language = normalize(old.language) if old.language is not None else None
    explicit_language = normalize(language) if language is not None else None
    package_language = (
        old.artifacts.package if old.project_kind in {"cli", "library"} and old.artifacts.package in _NATIVE else None
    )
    native_language = (
        next(
            (lang for lang, native in _NATIVE.items() if native in (old.cli_framework, old.framework, framework)), None
        )
        if old.project_kind == "cli"
        else None
    )
    selected_language = _choice(
        "project.language",
        [
            recorded_language,
            explicit_language,
            package_language,
            native_language,
            "typescript" if old.project_kind == "frontend" else None,
        ],
    )
    selected_framework = _choice(
        "project.framework",
        [
            old.framework,
            framework,
            old.cli_framework,
            _NATIVE.get(selected_language or "") if old.project_kind == "cli" else None,
            "react" if old.project_kind == "frontend" else None,
        ],
    )
    if old.project_kind == "system" and (selected_language is not None or selected_framework is not None):
        raise ManifestShapeError(
            "system roots are language-neutral; application identity cannot be migrated onto the root"
        )
    diagnostics: list[MigrationDiagnostic] = []
    if old.project_kind == "system" and "composition" not in source:
        diagnostics.append(
            MigrationDiagnostic(
                "composition",
                "unresolved-input",
                "Restore the recorded system composition before migrating; child discovery is not inferred.",
            )
        )
    if old.project_kind != "system" and selected_language is None:
        diagnostics.append(
            MigrationDiagnostic(
                "project.language", "unresolved-input", "Pass --language to resolve the missing recorded language."
            )
        )
    if old.project_kind == "service" and selected_language == "python" and selected_framework is None:
        diagnostics.append(
            MigrationDiagnostic(
                "project.framework",
                "unresolved-input",
                "Pass --framework fastapi or minimal to resolve the missing Python framework.",
            )
        )
    generated_by = old.generated_by
    semantics = source.get("semantics")
    if old.schema_version != "4.0" and semantics is not None:
        match = _SEMANTICS.fullmatch(cast(str, semantics))
        if match is None:
            raise ManifestShapeError("nonstandard semantics reference cannot be discarded; review it before migrating")
        recorded_version = "kickstart@" + match[1]
        if generated_by == "kickstart":
            generated_by = recorded_version
        elif generated_by.startswith("kickstart@") and generated_by != recorded_version:
            raise ManifestShapeError("generated_by conflicts with the version-pinned semantics reference")
    if generated_by == "kickstart":
        diagnostics.append(
            MigrationDiagnostic(
                "generated_by",
                "unknown-provenance",
                "Generating release remains explicitly unknown (kickstart).",
                blocking=False,
            )
        )
    composition = source.get("composition")
    contract = replace(
        old,
        schema_version="4.0",
        generated_by=generated_by,
        language=selected_language,
        framework=selected_framework,
        recorded_composition=cast(ScaffoldCompositionManifest, composition) if isinstance(composition, dict) else None,
    )
    return contract, tuple(diagnostics)
