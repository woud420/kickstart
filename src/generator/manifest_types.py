"""On-disk scaffold shapes shared by serialization and structural schema generation."""

from typing import Literal, NotRequired, TypedDict

ProjectKind = Literal["service", "worker", "frontend", "library", "cli", "system"]
RepoLayout = Literal["single-project", "monorepo"]
JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
ParsedManifest = dict[str, JsonValue]


class ScaffoldProjectFields(TypedDict):
    name: str
    repo_layout: RepoLayout
    language: NotRequired[str]
    framework: NotRequired[str]
    architecture: NotRequired[str]
    cli_framework: NotRequired[str]
    command_root: NotRequired[str]
    entrypoint: NotRequired[str]
    operation_root: NotRequired[str]
    src_root_files: NotRequired[list[str]]


class ScaffoldProjectManifest(ScaffoldProjectFields):
    kind: ProjectKind


class ScaffoldProjectV4(ScaffoldProjectFields):
    kind: Literal["service", "frontend", "library", "cli", "system"]


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


class ScaffoldServiceExtensionsManifest(TypedDict, total=False):
    database: str
    cache: str
    auth: str


class ScaffoldCapabilitiesManifest(TypedDict, total=False):
    service_extensions: ScaffoldServiceExtensionsManifest


class ScaffoldLifecycleManifest(TypedDict, total=False):
    install: str
    test: str
    check: str
    build: str
    dev: str
    deploy: str


class ScaffoldCompositionManifest(TypedDict):
    status: str
    workspace_tooling: str
    component_slots: list[str]
    child_manifest_globs: list[str]
    validation: str


class ScaffoldDocsManifest(TypedDict):
    agent_map: str
    architecture: str
    contracts: str
    operations: str
    decisions: str


class ScaffoldManifest(TypedDict):
    schema_version: str
    generated_by: str
    project: ScaffoldProjectManifest
    execution: ScaffoldExecutionManifest
    artifacts: ScaffoldArtifactsManifest
    provider: ScaffoldProviderManifest
    capabilities: ScaffoldCapabilitiesManifest
    lifecycle: ScaffoldLifecycleManifest
    knowledge_adapter: str
    docs: ScaffoldDocsManifest
    semantics: str


class SystemScaffoldManifest(ScaffoldManifest):
    composition: ScaffoldCompositionManifest


class ScaffoldManifestV4(TypedDict):
    schema_version: Literal["4.0"]
    generated_by: str
    project: ScaffoldProjectV4
    execution: ScaffoldExecutionManifest
    artifacts: ScaffoldArtifactsManifest
    provider: ScaffoldProviderManifest
    extensions: ScaffoldServiceExtensionsManifest
    lifecycle: ScaffoldLifecycleManifest
    knowledge_adapter: str
    composition: NotRequired[ScaffoldCompositionManifest]


ManifestPayload = ScaffoldManifest | ScaffoldManifestV4
