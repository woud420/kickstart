"""Creation failures must never announce success or publish a partial scaffold."""

from unittest.mock import Mock

import pytest

from src.generator.base import BaseGenerator
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract
from src.generator.template_plan import TemplatePlan
from src.utils.errors import ProjectCreationError


@pytest.fixture
def flow(monkeypatch):
    generator = BaseGenerator("flow-test", {})
    for name in (
        "create_project",
        "init_basic_structure",
        "write_templates_from_plan",
        "create_architecture_docs",
        "create_scaffold_contract_docs",
        "write_content",
        "log_success",
    ):
        monkeypatch.setattr(generator, name, Mock(return_value=True))
    options = {
        "directories": ["src"],
        "template_plan": TemplatePlan(()),
        "architecture_title": "Architecture",
        "scaffold_contract": ScaffoldContract(
            project_kind="service",
            language="python",
            framework="minimal",
            artifacts=ScaffoldArtifacts(image="dockerfile"),
            execution_models=("container",),
            runtime_platforms=("local",),
        ),
        "success_message": "Created",
        "language_setup_fn": Mock(return_value=True),
        "additional_setup_fn": Mock(return_value=True),
        "github_create_fn": Mock(return_value=True),
    }
    return generator, options


@pytest.mark.parametrize(
    "step",
    [
        "init_basic_structure",
        "write_templates_from_plan",
        "create_architecture_docs",
        "create_scaffold_contract_docs",
        "language_setup_fn",
        "additional_setup_fn",
    ],
)
@pytest.mark.parametrize("failure", [False, OSError("disk unavailable")])
def test_failed_step_blocks_success_ownership_and_remote(flow, step, failure):
    generator, options = flow
    operation = options[step] if step.endswith("_fn") else getattr(generator, step)
    if isinstance(failure, Exception):
        operation.side_effect = failure
    else:
        operation.return_value = failure

    with pytest.raises(ProjectCreationError, match="generated with errors"):
        generator.execute_create_flow(**options)

    generator.log_success.assert_not_called()
    generator.write_content.assert_not_called()
    options["github_create_fn"].assert_not_called()


def test_successful_flow_preserves_step_order(flow):
    generator, options = flow
    calls = []
    for name in (
        "create_project",
        "init_basic_structure",
        "write_templates_from_plan",
        "create_architecture_docs",
        "create_scaffold_contract_docs",
        "write_content",
        "log_success",
    ):
        getattr(generator, name).side_effect = lambda *args, step=name: calls.append(step) or True
    for name in ("language_setup_fn", "additional_setup_fn", "github_create_fn"):
        options[name].side_effect = lambda step=name: calls.append(step) or True

    assert generator.execute_create_flow(**options) is True
    assert calls == [
        "create_project",
        "init_basic_structure",
        "write_templates_from_plan",
        "create_architecture_docs",
        "create_scaffold_contract_docs",
        "language_setup_fn",
        "additional_setup_fn",
        "write_content",
        "log_success",
        "github_create_fn",
    ]


def test_creation_collects_multiple_failures(flow):
    generator, options = flow
    generator.create_architecture_docs.side_effect = OSError("missing template")
    options["language_setup_fn"].return_value = False

    with pytest.raises(ProjectCreationError) as caught:
        generator.execute_create_flow(**options)

    assert "architecture documentation" in str(caught.value)
    assert "Language-specific setup failed" in str(caught.value)
    options["additional_setup_fn"].assert_called_once()
    options["github_create_fn"].assert_not_called()


def test_missing_optional_steps_remain_optional(flow):
    generator, options = flow
    options.update(language_setup_fn=None, additional_setup_fn=None, github_create_fn=None)
    assert generator.execute_create_flow(**options) is True
    generator.log_success.assert_called_once_with("Created")


def test_step_that_drops_a_write_fails_even_when_it_returns_true(flow):
    generator, options = flow
    options["language_setup_fn"].side_effect = lambda: generator._record_write("Cargo.toml", False) or True

    with pytest.raises(ProjectCreationError, match="Language-specific setup failed: could not write Cargo.toml"):
        generator.execute_create_flow(**options)

    generator.log_success.assert_not_called()
    options["github_create_fn"].assert_not_called()
