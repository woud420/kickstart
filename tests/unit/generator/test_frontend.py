from types import SimpleNamespace
from unittest.mock import call, patch

import pytest

from src.generator.frontend import FrontendGenerator
from src.utils.errors import ProjectCreationError


@pytest.fixture
def frontend_generator():
    return FrontendGenerator("test-frontend", False, {"key": "value"})


@pytest.fixture(autouse=True)
def mock_scaffold_contract_docs():
    with patch.object(FrontendGenerator, "create_scaffold_contract_docs", return_value=True):
        yield


@pytest.fixture
def create_mocks():
    with (
        patch.object(FrontendGenerator, "create_project", return_value=True) as create_project,
        patch.object(FrontendGenerator, "init_basic_structure") as init_basic_structure,
        patch.object(FrontendGenerator, "write_template") as write_template,
        patch.object(FrontendGenerator, "create_architecture_docs") as create_architecture_docs,
        patch.object(FrontendGenerator, "log_success") as log_success,
    ):
        yield SimpleNamespace(
            create_project=create_project,
            init_basic_structure=init_basic_structure,
            write_template=write_template,
            create_architecture_docs=create_architecture_docs,
            log_success=log_success,
        )


@pytest.mark.parametrize("gh", [True, False], ids=["with-gh", "without-gh"])
@patch("src.generator.frontend.create_repo")
def test_create_success(mock_create_repo, create_mocks, gh):
    generator = FrontendGenerator("test-frontend", gh, {"key": "value"})

    generator.create()

    create_mocks.create_project.assert_called_once()
    create_mocks.init_basic_structure.assert_called_once_with(
        [
            "src",
            "public",
            "tests",
            ".kickstart",
            ".agents/skills",
            "docs/architecture",
            "docs/contracts",
            "docs/operations",
            "docs/decisions",
        ]
    )
    expected_template_calls = [
        call("index.html", "index.html.tpl"),
        call(".gitignore", "gitignore.tpl"),
        call("Dockerfile", "Dockerfile.tpl"),
        call("Makefile", "Makefile.tpl", has_docker=True),
        call("README.md", "README.md.tpl"),
        call("package.json", "package.json.tpl"),
        call("tsconfig.json", "tsconfig.json.tpl"),
        call("vite.config.ts", "vite.config.ts.tpl"),
        call("src/App.tsx", "src/App.tsx.tpl"),
        call("src/main.tsx", "src/main.tsx.tpl"),
        call("tests/App.test.tsx", "tests/App.test.tsx.tpl"),
    ]
    create_mocks.write_template.assert_has_calls(expected_template_calls, any_order=True)
    create_mocks.create_architecture_docs.assert_called_once()
    assert create_mocks.create_architecture_docs.call_args.args[0] == "test-frontend Frontend Docs"
    create_mocks.log_success.assert_called_once_with(
        "Frontend app 'test-frontend' created successfully in 'test-frontend'!"
    )
    if gh:
        mock_create_repo.assert_called_once_with("test-frontend")
    else:
        mock_create_repo.assert_not_called()


@patch.object(FrontendGenerator, "create_project")
def test_create_fails_when_create_project_fails(mock_create_project, frontend_generator):
    mock_create_project.return_value = False

    with pytest.raises(ProjectCreationError, match="was not created"):
        frontend_generator.create()

    mock_create_project.assert_called_once()


def test_architecture_docs_content(create_mocks):
    generator = FrontendGenerator("my-awesome-app", False, {})
    generator.create()

    create_mocks.create_architecture_docs.assert_called_once()
    assert create_mocks.create_architecture_docs.call_args.args[0] == "my-awesome-app Frontend Docs"


def test_frontend_html_loads_a_generated_module(tmp_path):
    from html.parser import HTMLParser

    entries = []

    class ModuleScripts(HTMLParser):
        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if tag == "script" and attributes.get("type") == "module" and attributes.get("src"):
                entries.append(attributes["src"])

    FrontendGenerator("dashboard", False, {}, root=str(tmp_path)).create()
    project = tmp_path / "dashboard"
    ModuleScripts().feed((project / "index.html").read_text())
    assert entries, "index.html has no module entry point"
    for entry in entries:
        module = (project / entry.lstrip("/")).resolve()
        assert module.is_relative_to(project)
        assert module.is_file(), f"Missing frontend entry point: {entry}"
