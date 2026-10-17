"""Machine-readable scaffold contract metadata for generated projects."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import cast

from src import __version__
from src.utils.errors import ManifestShapeError
from src.generator.manifest_types import (
    JsonValue,
    MANIFEST_PATH as MANIFEST_PATH,
    OwnershipManifest,
    ManifestPayload,
    ParsedManifest,
    ProjectKind,
    RepoLayout,
    ScaffoldArtifactsManifest,
    ScaffoldCapabilitiesManifest,
    ScaffoldCompositionManifest,
    ScaffoldLifecycleManifest,
    ScaffoldManifest,
    ScaffoldManifestV4,
    ScaffoldProjectManifest,
    ScaffoldProjectV4,
    ScaffoldServiceExtensionsManifest,
    SystemScaffoldManifest,
)
from src.generator.manifest_schema import validate_v4_manifest
from src.generator.ownership_plan import OwnershipRecord, ownership_from_manifest

# Field meanings live in one place instead of being duplicated into every
# generated repo; the manifest carries this pointer so agents can resolve the
# vocabulary without kickstart re-emitting it per project. Pinned to the
# generating version's tag so the referenced semantics cannot drift under a
# manifest that has already been written.
SEMANTICS_REFERENCE = f"https://github.com/woud420/kickstart/blob/v{__version__}/docs/scaffold-contract.md"

_PROJECT_KINDS: frozenset[str] = frozenset({"service", "worker", "frontend", "library", "cli", "system"})
_REPO_LAYOUTS: frozenset[str] = frozenset({"single-project", "monorepo"})

def load_parsed_manifest(manifest_file: "Path") -> ParsedManifest:
    """Read and parse an on-disk scaffold manifest, fail-closed.

    The single loader both `adopt --check` and `plan` sit on, so the two
    commands can never disagree about what counts as a readable manifest.
    Raises ``ManifestShapeError`` with a human-readable reason.
    """
    try:
        parsed = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        raise ManifestShapeError(f"unreadable manifest: {error}") from error
    except json.JSONDecodeError as error:
        raise ManifestShapeError(f"manifest is not valid JSON: {error}") from error
    if not isinstance(parsed, dict):
        raise ManifestShapeError("manifest is not a JSON object")
    return parsed


def _require_mapping(value: "JsonValue | None", description: str) -> ParsedManifest:
    """Return the value as a JSON object or fail with its manifest path."""
    if not isinstance(value, dict):
        raise ManifestShapeError(f"manifest {description} is not an object")
    return value


def _optional_string(mapping: ParsedManifest, key: str) -> str | None:
    """Return a string field or None; a present non-string value is a shape error."""
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ManifestShapeError(f"manifest field '{key}' is not a string")
    return value


def _string_items(value: "JsonValue | None", description: str) -> tuple[str, ...]:
    """Return a list-of-strings field as a tuple, failing on other shapes."""
    if not isinstance(value, list):
        raise ManifestShapeError(f"manifest {description} is not a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ManifestShapeError(f"manifest {description} is not a list of strings")
        items.append(item)
    return tuple(items)


@dataclass(frozen=True)
class ScaffoldArtifacts:
    """Typed artifact set emitted by a scaffold."""

    image: str | None = None
    kubernetes: str | None = None
    local: str | None = None
    package: str | None = None
    static_site: str | None = None
    worker: str | None = None
    iac: str | None = None
    ci: str | None = None

    def manifest(self) -> ScaffoldArtifactsManifest:
        """Return JSON-ready artifact fields without empty values."""
        manifest: ScaffoldArtifactsManifest = {}
        if self.image is not None:
            manifest["image"] = self.image
        if self.kubernetes is not None:
            manifest["kubernetes"] = self.kubernetes
        if self.local is not None:
            manifest["local"] = self.local
        if self.package is not None:
            manifest["package"] = self.package
        if self.static_site is not None:
            manifest["static_site"] = self.static_site
        if self.worker is not None:
            manifest["worker"] = self.worker
        if self.iac is not None:
            manifest["iac"] = self.iac
        if self.ci is not None:
            manifest["ci"] = self.ci
        return manifest


@dataclass(frozen=True)
class ScaffoldLifecycle:
    """Lifecycle commands emitted by a scaffold."""

    install: str | None = None
    test: str | None = None
    check: str | None = None
    build: str | None = None
    dev: str | None = None
    deploy: str | None = None

    def manifest(self) -> ScaffoldLifecycleManifest:
        """Return JSON-ready lifecycle commands without empty values."""
        manifest: ScaffoldLifecycleManifest = {}
        if self.install is not None:
            manifest["install"] = self.install
        if self.test is not None:
            manifest["test"] = self.test
        if self.check is not None:
            manifest["check"] = self.check
        if self.build is not None:
            manifest["build"] = self.build
        if self.dev is not None:
            manifest["dev"] = self.dev
        if self.deploy is not None:
            manifest["deploy"] = self.deploy
        return manifest


@dataclass(frozen=True)
class ScaffoldServiceExtensions:
    """Service extensions selected for a generated scaffold."""

    database: str | None = None
    cache: str | None = None
    auth: str | None = None

    def manifest(self) -> ScaffoldServiceExtensionsManifest:
        """Return JSON-ready extension fields without empty values."""
        manifest: ScaffoldServiceExtensionsManifest = {}
        if self.database is not None:
            manifest["database"] = self.database
        if self.cache is not None:
            manifest["cache"] = self.cache
        if self.auth is not None:
            manifest["auth"] = self.auth
        return manifest


@dataclass(frozen=True)
class ScaffoldContract:
    """Explicit contract for generated project shape and option vocabulary."""

    project_kind: ProjectKind
    execution_models: tuple[str, ...]
    runtime_platforms: tuple[str, ...]
    artifacts: ScaffoldArtifacts = field(default_factory=ScaffoldArtifacts)
    lifecycle: ScaffoldLifecycle | None = None
    service_extensions: ScaffoldServiceExtensions = field(default_factory=ScaffoldServiceExtensions)
    provider_targets: tuple[str, ...] = ()
    knowledge_adapter: str = "none"
    repo_layout: RepoLayout = "single-project"
    workspace_tooling: str = "none"
    architecture: str | None = None
    cli_framework: str | None = None
    command_root: str | None = None
    entrypoint: str | None = None
    operation_root: str | None = None
    src_root_files: tuple[str, ...] = ()
    schema_version: str = "4.0"
    generated_by: str = f"kickstart@{__version__}"
    semantics_reference: str = SEMANTICS_REFERENCE
    language: str | None = None
    framework: str | None = None
    recorded_composition: ScaffoldCompositionManifest | None = None
    ownership: tuple[OwnershipRecord, ...] | None = None

    def manifest(self, project_name: str) -> ManifestPayload:
        """Return the JSON-serializable scaffold manifest."""
        project_manifest: ScaffoldProjectManifest = {
            "name": project_name,
            "kind": self.project_kind,
            "repo_layout": self.repo_layout,
        }
        if self.language is not None:
            project_manifest["language"] = self.language
        if self.framework is not None:
            project_manifest["framework"] = self.framework
        if self.architecture is not None:
            project_manifest["architecture"] = self.architecture
        if self.cli_framework is not None:
            project_manifest["cli_framework"] = self.cli_framework
        if self.command_root is not None:
            project_manifest["command_root"] = self.command_root
        if self.entrypoint is not None:
            project_manifest["entrypoint"] = self.entrypoint
        if self.operation_root is not None:
            project_manifest["operation_root"] = self.operation_root
        if self.src_root_files:
            project_manifest["src_root_files"] = list(self.src_root_files)

        manifest: ScaffoldManifest = {
            "schema_version": self.schema_version,
            "generated_by": self.generated_by,
            "project": project_manifest,
            "execution": {
                "models": list(self.execution_models),
                "platforms": list(self.runtime_platforms),
            },
            "artifacts": self.artifacts.manifest(),
            "provider": {"targets": list(self.provider_targets)},
            "capabilities": self._capabilities_manifest(),
            "lifecycle": self.resolved_lifecycle().manifest(),
            "knowledge_adapter": self.knowledge_adapter,
            "docs": {
                "agent_map": "AGENTS.md",
                "architecture": "docs/architecture/",
                "contracts": "docs/contracts/",
                "operations": "docs/operations/",
                "decisions": "docs/decisions/",
            },
            "semantics": self.semantics_reference,
        }
        if self.project_kind == "system":
            system_manifest = SystemScaffoldManifest(
                **manifest,
                composition=self.recorded_composition or {
                    "status": "experimental",
                    "workspace_tooling": self.workspace_tooling,
                    "component_slots": ["apps", "services", "libs", "tools"],
                    "child_manifest_globs": [
                        "apps/*/.kickstart/scaffold.json",
                        "services/*/.kickstart/scaffold.json",
                        "libs/*/.kickstart/scaffold.json",
                        "tools/*/.kickstart/scaffold.json",
                    ],
                    "validation": (
                        "System roots validate scaffold files only. Validate contained projects "
                        "by reading child manifests and running their lifecycle commands."
                    ),
                },
            )
            manifest = system_manifest
        if self.schema_version == "4.0":
            v4_project = cast(ScaffoldProjectV4, dict(project_manifest))
            if self.is_worker:
                v4_project["kind"] = "service"
            v4: ScaffoldManifestV4 = {
                "schema_version": "4.0",
                "generated_by": self.generated_by,
                "project": v4_project,
                "execution": manifest["execution"],
                "artifacts": manifest["artifacts"],
                "provider": manifest["provider"],
                "extensions": self.service_extensions.manifest(),
                "lifecycle": manifest["lifecycle"],
                "knowledge_adapter": self.knowledge_adapter,
            }
            if self.project_kind == "system":
                v4["composition"] = system_manifest["composition"]
            if self.ownership is not None:
                v4["ownership"] = {record.path: record.manifest() for record in self.ownership}
            validate_v4_manifest(cast(ParsedManifest, v4))
            return v4
        return manifest

    def _capabilities_manifest(self) -> ScaffoldCapabilitiesManifest:
        """Return generated optional capability metadata."""
        service_extensions = self.service_extensions.manifest()
        if service_extensions:
            return {"service_extensions": service_extensions}
        return {}

    def manifest_json(self, project_name: str) -> str:
        """Return stable, pretty JSON for `.kickstart/scaffold.json`."""
        return json.dumps(self.manifest(project_name), indent=2, sort_keys=True) + "\n"

    def resolved_lifecycle(self) -> ScaffoldLifecycle:
        """Return the effective lifecycle commands (explicit or kind defaults)."""
        if self.lifecycle is not None:
            return self.lifecycle

        if self.project_kind == "system":
            return ScaffoldLifecycle(
                install="make install",
                test="make test",
                check="make check",
            )

        if self.project_kind in {"service", "frontend"} and not self.is_worker:
            return ScaffoldLifecycle(
                install="make install",
                test="make test",
                check="make check",
                build="make build",
                dev="make dev",
            )

        if self.is_worker:
            return ScaffoldLifecycle(
                install="make install",
                test="make test",
                check="make check",
                dev="make dev",
                deploy="make deploy",
            )

        return ScaffoldLifecycle(
            install="make install",
            test="make test",
            check="make check",
        )

    @classmethod
    def from_manifest(cls, manifest: ParsedManifest) -> "ScaffoldContract":
        """Rebuild the contract fields tooling consumes from a parsed manifest.

        Inverse of ``manifest()`` for supported schema 3.x and 4.0, written defensively because
        the input is an on-disk file: required keys and shapes raise
        ``ManifestShapeError`` instead of guessing. Generation-time inputs the
        manifest never recorded (docs projection profile, architecture title
        and directories) cannot be recovered here; consumers own that gap.
        """
        schema_version = manifest.get("schema_version")
        if not isinstance(schema_version, str) or schema_version not in {"3.0", "3.1", "3.2", "4.0"}:
            raise ManifestShapeError(f"unsupported manifest schema_version: {schema_version!r}")
        if schema_version == "4.0":
            validate_v4_manifest(manifest)
        project = _require_mapping(manifest.get("project"), "project")
        execution = _require_mapping(manifest.get("execution"), "execution")
        kind = project.get("kind")
        if not isinstance(kind, str) or kind not in _PROJECT_KINDS:
            raise ManifestShapeError(f"unsupported project.kind: {kind!r}")
        repo_layout = project.get("repo_layout", "single-project")
        if not isinstance(repo_layout, str) or repo_layout not in _REPO_LAYOUTS:
            raise ManifestShapeError(f"unsupported project.repo_layout: {repo_layout!r}")

        artifacts = _require_mapping(manifest.get("artifacts", {}), "artifacts")
        lifecycle = _require_mapping(manifest.get("lifecycle", {}), "lifecycle")
        if schema_version == "4.0":
            extensions = _require_mapping(manifest.get("extensions"), "extensions")
        else:
            if "extensions" in manifest:
                raise ManifestShapeError("manifest extensions requires schema_version 4.0")
            capabilities = _require_mapping(manifest.get("capabilities", {}), "capabilities")
            extensions = _require_mapping(
                capabilities.get("service_extensions", {}), "capabilities.service_extensions"
            )
        provider = _require_mapping(manifest.get("provider", {}), "provider")

        workspace_tooling = "none"
        composition = manifest.get("composition")
        if isinstance(composition, dict):
            tooling = composition.get("workspace_tooling")
            if isinstance(tooling, str):
                workspace_tooling = tooling

        knowledge_adapter = manifest.get("knowledge_adapter", "none")
        if not isinstance(knowledge_adapter, str):
            raise ManifestShapeError("manifest field 'knowledge_adapter' is not a string")
        framework = _optional_string(project, "framework")
        cli_framework = _optional_string(project, "cli_framework")
        if kind == "cli" and framework is not None and cli_framework is not None and framework != cli_framework:
            raise ManifestShapeError("manifest project.framework and project.cli_framework disagree")

        generated_by = manifest.get("generated_by", "kickstart")
        if not isinstance(generated_by, str):
            raise ManifestShapeError("manifest field 'generated_by' is not a string")

        return cls(
            project_kind=cast(ProjectKind, kind),
            execution_models=_string_items(execution.get("models", []), "execution.models"),
            runtime_platforms=_string_items(execution.get("platforms", []), "execution.platforms"),
            artifacts=ScaffoldArtifacts(
                image=_optional_string(artifacts, "image"),
                kubernetes=_optional_string(artifacts, "kubernetes"),
                local=_optional_string(artifacts, "local"),
                package=_optional_string(artifacts, "package"),
                static_site=_optional_string(artifacts, "static_site"),
                worker=_optional_string(artifacts, "worker"),
                iac=_optional_string(artifacts, "iac"),
                ci=_optional_string(artifacts, "ci"),
            ),
            lifecycle=ScaffoldLifecycle(
                install=_optional_string(lifecycle, "install"),
                test=_optional_string(lifecycle, "test"),
                check=_optional_string(lifecycle, "check"),
                build=_optional_string(lifecycle, "build"),
                dev=_optional_string(lifecycle, "dev"),
                deploy=_optional_string(lifecycle, "deploy"),
            ),
            service_extensions=ScaffoldServiceExtensions(
                database=_optional_string(extensions, "database"),
                cache=_optional_string(extensions, "cache"),
                auth=_optional_string(extensions, "auth"),
            ),
            provider_targets=_string_items(provider.get("targets", []), "provider.targets"),
            knowledge_adapter=knowledge_adapter,
            repo_layout=cast(RepoLayout, repo_layout),
            workspace_tooling=workspace_tooling,
            architecture=_optional_string(project, "architecture"),
            cli_framework=cli_framework,
            command_root=_optional_string(project, "command_root"),
            entrypoint=_optional_string(project, "entrypoint"),
            operation_root=_optional_string(project, "operation_root"),
            src_root_files=_string_items(project.get("src_root_files", []), "project.src_root_files"),
            schema_version=schema_version,
            generated_by=generated_by,
            semantics_reference=_optional_string(manifest, "semantics") or SEMANTICS_REFERENCE,
            language=_optional_string(project, "language"),
            framework=framework,
            ownership=ownership_from_manifest(cast(OwnershipManifest | None, manifest.get("ownership"))) if schema_version == "4.0" else None,
            recorded_composition=(
                cast(ScaffoldCompositionManifest, composition)
                if schema_version == "4.0" and isinstance(composition, dict) else None
            ),
        )

    @property
    def is_worker(self) -> bool:
        """Recognize both the legacy kind and the service execution profile."""
        return self.project_kind == "worker" or (
            self.project_kind == "service" and "cloudflare-worker" in self.execution_models
        )

    @property
    def contract_subjects(self) -> str:
        """Return project-type-specific contract guidance."""
        subjects = {
            "service": "HTTP APIs, environment variables, commands, ports, files, queues, and service boundaries",
            "worker": "Worker routes, bindings, environment variables, commands, files, and edge runtime boundaries",
            "frontend": "routes, public environment variables, build commands, static assets, and backend API assumptions",
            "library": "public APIs, package metadata, supported versions, commands, and generated files",
            "cli": "commands, flags, environment variables, config files, exit codes, and package metadata",
            "system": "workspace interfaces, contained projects, service boundaries, environment variables, commands, provider resources, and generated files",
        }
        return subjects["worker" if self.is_worker else self.project_kind]

    @property
    def operations_subjects(self) -> str:
        """Return project-type-specific operations guidance."""
        subjects = {
            "service": "local development, tests, container builds, dependency services, and deployment notes",
            "worker": "local Wrangler development, tests, bindings, and deploy notes",
            "frontend": "local development, tests, builds, preview commands, and deploy notes",
            "library": "local development, tests, packaging, versioning, and release notes",
            "cli": "local development, tests, packaging, installation, and release notes",
            "system": "workspace composition, root scaffold checks, child project validation, infrastructure notes, and runbooks",
        }
        return subjects["worker" if self.is_worker else self.project_kind]
