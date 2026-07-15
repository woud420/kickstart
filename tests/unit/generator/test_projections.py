"""The managed docs projection registry: pure, enumerable, deterministic."""

from src.generator.layouts import render_architecture_readme, service_directories
from src.generator.markers import fence, find_fenced_region
from src.generator.projections import (
    PROFILE_DEFAULT,
    PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER,
    agent_map_content,
    architecture_readme_projection,
    contracts_content,
    decisions_content,
    operations_content,
    scaffold_docs_projections,
)
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract


def _service_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
        artifacts=ScaffoldArtifacts(image="dockerfile"),
    )


def _cli_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="cli",
        execution_models=("cli",),
        runtime_platforms=("local",),
        architecture="modular-cli",
        cli_framework="typer",
        command_root="src/cli/commands",
        entrypoint="src/main.py",
        operation_root="src/operations",
    )


def _worker_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="worker",
        execution_models=("cloudflare-worker",),
        runtime_platforms=("cloudflare-workers",),
        artifacts=ScaffoldArtifacts(worker="wrangler"),
        provider_targets=("cloudflare",),
    )


def test_registry_ids_and_targets_are_stable() -> None:
    projections = scaffold_docs_projections(_service_contract())

    assert [projection.id for projection in projections] == [
        "agent-map",
        "contracts-readme",
        "operations-readme",
        "decisions-readme",
    ]
    assert [projection.target for projection in projections] == [
        "AGENTS.md",
        "docs/contracts/README.md",
        "docs/operations/README.md",
        "docs/decisions/README.md",
    ]


def test_renders_are_deterministic_across_kinds_and_profiles() -> None:
    cases = (
        (_service_contract(), PROFILE_DEFAULT),
        (_cli_contract(), PROFILE_DEFAULT),
        (_worker_contract(), PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER),
    )
    for contract, profile in cases:
        first = scaffold_docs_projections(contract, profile)
        second = scaffold_docs_projections(contract, profile)
        assert first == second, f"non-deterministic render for {contract.project_kind}/{profile}"


def test_default_agent_map_is_orientation_first() -> None:
    content = agent_map_content()

    assert "docs/architecture/" in content
    assert "orientation surface" in content
    assert "before changing generated conventions" not in content


def test_worker_profile_variants_are_contract_gated() -> None:
    worker = _worker_contract()
    service = _service_contract()
    profile = PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER

    assert "Do not hand-edit generated contract files" in agent_map_content(profile)
    assert "Scaffold identity" in contracts_content(worker, profile)
    assert "Lifecycle flow" in operations_content(worker, profile)
    # Contracts/operations variants require a worker-kind contract; other
    # kinds render the defaults even under the worker profile.
    assert "Scaffold identity" not in contracts_content(service, profile)
    assert "Lifecycle flow" not in operations_content(service, profile)


def test_cli_contract_renders_framework_boundaries() -> None:
    content = contracts_content(_cli_contract())

    assert "`typer`" in content
    assert "`src/cli/commands`" in content
    assert "`src/operations`" in content
    assert "`src/main.py`" in content


def test_architecture_projection_matches_layout_render() -> None:
    contract = _service_contract()
    directories = service_directories()

    projection = architecture_readme_projection("api Architecture", directories, contract)

    assert projection.id == "architecture-readme"
    assert projection.target == "docs/architecture/README.md"
    assert projection.content == fence(
        "architecture-readme", render_architecture_readme("api Architecture", directories, contract)
    )


def test_projection_contents_are_single_owned_regions() -> None:
    projections = scaffold_docs_projections(_service_contract())

    for projection in projections:
        region = find_fenced_region(projection.content, projection.id)
        assert region is not None, f"{projection.id} content is not fenced"
        # The generated file is exactly one owned region: fence + body, nothing outside.
        assert projection.content == fence(projection.id, region.inner)
    agent_map = projections[0]
    region = find_fenced_region(agent_map.content, "agent-map")
    assert region is not None
    assert region.inner == agent_map_content()


def test_decisions_content_asks_for_durable_entries() -> None:
    content = decisions_content()

    assert content.startswith("# Decisions")
    assert "short, dated" in content
