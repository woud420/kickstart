"""Machine-readable scaffold contract metadata for generated projects."""

from dataclasses import dataclass
import json
from typing import Literal, TypedDict


ProjectKind = Literal["service", "worker", "frontend", "library", "cli", "monorepo"]


class ScaffoldProjectManifest(TypedDict):
    name: str
    type: ProjectKind


class ScaffoldOptionsManifest(TypedDict):
    runtime: str
    deploy: str
    cloud: str
    knowledge_adapter: str


class ScaffoldDocsManifest(TypedDict):
    agent_map: str
    architecture: str
    contracts: str
    operations: str
    decisions: str


class ScaffoldOptionSemanticsManifest(TypedDict):
    runtime: str
    deploy: str
    cloud: str
    knowledge_adapter: str


class ScaffoldManifest(TypedDict):
    schema_version: str
    generated_by: str
    project: ScaffoldProjectManifest
    options: ScaffoldOptionsManifest
    docs: ScaffoldDocsManifest
    option_semantics: ScaffoldOptionSemanticsManifest


@dataclass(frozen=True)
class ScaffoldContract:
    """Explicit contract for generated project shape and option vocabulary."""

    project_kind: ProjectKind
    runtime: str
    deploy: str = "none"
    cloud: str = "none"
    knowledge_adapter: str = "none"
    schema_version: str = "1.0"

    def manifest(self, project_name: str) -> ScaffoldManifest:
        """Return the JSON-serializable scaffold manifest."""
        return {
            "schema_version": self.schema_version,
            "generated_by": "kickstart",
            "project": {
                "name": project_name,
                "type": self.project_kind,
            },
            "options": {
                "runtime": self.runtime,
                "deploy": self.deploy,
                "cloud": self.cloud,
                "knowledge_adapter": self.knowledge_adapter,
            },
            "docs": {
                "agent_map": "AGENTS.md",
                "architecture": "docs/architecture/",
                "contracts": "docs/contracts/",
                "operations": "docs/operations/",
                "decisions": "docs/decisions/",
            },
            "option_semantics": {
                "runtime": "how code executes",
                "deploy": "what deployment artifacts are emitted",
                "cloud": "provider or infrastructure target",
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
            "monorepo": "workspace interfaces, service boundaries, environment variables, commands, cloud resources, and generated files",
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
            "monorepo": "workspace development, tests, infrastructure validation, deployment notes, and runbooks",
        }
        return subjects[self.project_kind]
