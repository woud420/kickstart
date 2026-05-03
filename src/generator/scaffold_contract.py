"""Machine-readable scaffold contract metadata for generated projects."""

from dataclasses import dataclass, field
import json
from typing import Literal, TypedDict


ProjectKind = Literal["service", "worker", "frontend", "library", "cli", "system"]
RepoLayout = Literal["single-project", "monorepo"]


class ScaffoldProjectManifest(TypedDict):
    name: str
    kind: ProjectKind
    repo_layout: RepoLayout


class ScaffoldExecutionManifest(TypedDict):
    models: list[str]
    platforms: list[str]


class ScaffoldArtifactsManifest(TypedDict, total=False):
    image: str
    kubernetes: str
    local: str
    package: str
    static_site: str
    worker: str
    iac: str
    ci: str


class ScaffoldProviderManifest(TypedDict):
    targets: list[str]


class ScaffoldDocsManifest(TypedDict):
    agent_map: str
    architecture: str
    contracts: str
    operations: str
    decisions: str


class ScaffoldOptionSemanticsManifest(TypedDict):
    project_kind: str
    repo_layout: str
    execution_models: str
    runtime_platforms: str
    artifacts: str
    provider_targets: str
    knowledge_adapter: str


class ScaffoldManifest(TypedDict):
    schema_version: str
    generated_by: str
    project: ScaffoldProjectManifest
    execution: ScaffoldExecutionManifest
    artifacts: ScaffoldArtifactsManifest
    provider: ScaffoldProviderManifest
    knowledge_adapter: str
    docs: ScaffoldDocsManifest
    option_semantics: ScaffoldOptionSemanticsManifest


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
class ScaffoldContract:
    """Explicit contract for generated project shape and option vocabulary."""

    project_kind: ProjectKind
    execution_models: tuple[str, ...]
    runtime_platforms: tuple[str, ...]
    artifacts: ScaffoldArtifacts = field(default_factory=ScaffoldArtifacts)
    provider_targets: tuple[str, ...] = ()
    knowledge_adapter: str = "none"
    repo_layout: RepoLayout = "single-project"
    schema_version: str = "2.0"

    def manifest(self, project_name: str) -> ScaffoldManifest:
        """Return the JSON-serializable scaffold manifest."""
        return {
            "schema_version": self.schema_version,
            "generated_by": "kickstart",
            "project": {
                "name": project_name,
                "kind": self.project_kind,
                "repo_layout": self.repo_layout,
            },
            "execution": {
                "models": list(self.execution_models),
                "platforms": list(self.runtime_platforms),
            },
            "artifacts": self.artifacts.manifest(),
            "provider": {"targets": list(self.provider_targets)},
            "knowledge_adapter": self.knowledge_adapter,
            "docs": {
                "agent_map": "AGENTS.md",
                "architecture": "docs/architecture/",
                "contracts": "docs/contracts/",
                "operations": "docs/operations/",
                "decisions": "docs/decisions/",
            },
            "option_semantics": {
                "project_kind": "what kickstart generated",
                "repo_layout": "how generated projects are arranged in the repository",
                "execution_models": "how generated code is meant to execute",
                "runtime_platforms": "where generated runtime artifacts are meant to run",
                "artifacts": "files and tool configs emitted by the scaffold",
                "provider_targets": "infrastructure providers targeted by generated IaC or platform config",
                "knowledge_adapter": "external knowledge integration metadata",
            },
        }

    def manifest_json(self, project_name: str) -> str:
        """Return stable, pretty JSON for `.kickstart/scaffold.json`."""
        return json.dumps(self.manifest(project_name), indent=2, sort_keys=True) + "\n"

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
        return subjects[self.project_kind]

    @property
    def operations_subjects(self) -> str:
        """Return project-type-specific operations guidance."""
        subjects = {
            "service": "local development, tests, container builds, dependency services, and deployment notes",
            "worker": "local Wrangler development, tests, bindings, and deploy notes",
            "frontend": "local development, tests, builds, preview commands, and deploy notes",
            "library": "local development, tests, packaging, versioning, and release notes",
            "cli": "local development, tests, packaging, installation, and release notes",
            "system": "workspace development, tests, infrastructure validation, deployment notes, and runbooks",
        }
        return subjects[self.project_kind]
