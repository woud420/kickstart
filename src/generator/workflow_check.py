"""Inspect declared CI job identities without evaluating or comparing workflows."""

from dataclasses import dataclass

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode


_STANDARD_JOBS = {
    ".github/workflows/ci.yml": "check",
    ".github/workflows/build.yml": "workspace",
    ".github/workflows/test.yml": "generated-contracts",
    ".github/workflows/deploy.yml": "plan",
}


@dataclass(frozen=True)
class WorkflowCheck:
    ok: bool
    detail: str


def _mapping(node: Node | None) -> dict[str, Node] | None:
    if not isinstance(node, MappingNode):
        return None
    result: dict[str, Node] = {}
    for key, value in node.value:
        if not isinstance(key, ScalarNode) or key.value in result:
            return None
        result[key.value] = value
    return result


def inspect_workflow(text: str, target: str) -> WorkflowCheck:
    # Compose nodes only: repository YAML must never construct Python objects.
    try:
        document = _mapping(yaml.compose(text, Loader=yaml.BaseLoader))
    except (yaml.YAMLError, RecursionError):
        return WorkflowCheck(False, "workflow is not parseable single-document YAML")
    if document is None:
        return WorkflowCheck(False, "workflow requires a mapping with unique scalar keys")
    jobs = _mapping(document.get("jobs"))
    if not jobs:
        return WorkflowCheck(False, "workflow has no unambiguous jobs mapping")
    expected = _STANDARD_JOBS.get(target)
    if expected is not None and not isinstance(jobs.get(expected), MappingNode):
        return WorkflowCheck(False, f"standard job '{expected}' is absent or is not a mapping")
    if not all(isinstance(job, MappingNode) for job in jobs.values()):
        return WorkflowCheck(False, "workflow job declarations must be mappings")
    detail = f"standard job '{expected}' declared" if expected else "workflow job mapping declared"
    return WorkflowCheck(True, detail + "; execution, steps and graph are not evaluated")
