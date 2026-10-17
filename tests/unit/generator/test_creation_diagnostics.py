"""Required setup errors retain their diagnostic through creation orchestration."""

from contextlib import suppress
import logging
from unittest.mock import Mock

from src.generator.base import BaseGenerator
from src.generator.scaffold_contract import ScaffoldContract
from src.generator.template_plan import TemplatePlan
from src.utils.errors import ProjectCreationError


def test_creation_reports_required_setup_error(monkeypatch, caplog):
    generator = BaseGenerator("diagnostic-service", {})
    for method in (
        "create_project",
        "init_basic_structure",
        "write_templates_from_plan",
        "create_architecture_docs",
        "create_scaffold_contract_docs",
        "create_with_github",
    ):
        monkeypatch.setattr(generator, method, Mock(return_value=True))
    setup = Mock(side_effect=ValueError("setup exploded"))
    contract = ScaffoldContract(
        schema_version="3.2",
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
    )

    with caplog.at_level(logging.ERROR), suppress(ProjectCreationError):
        generator.execute_create_flow(
            directories=(),
            template_plan=TemplatePlan(()),
            architecture_title="Diagnostic service",
            scaffold_contract=contract,
            success_message="Created",
            language_setup_fn=setup,
        )

    setup.assert_called_once_with()
    assert any("setup exploded" in record.getMessage() for record in caplog.records)
