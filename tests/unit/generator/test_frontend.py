from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

import pytest

from src.generator.frontend import FrontendGenerator
from src.utils.errors import ProjectCreationError


@pytest.fixture
def frontend_generator():
    return FrontendGenerator("test-frontend", False, {"key": "value"})


@pytest.fixture
def frontend_generator_with_gh():
    return FrontendGenerator("test-frontend", True, {"key": "value"})


@pytest.fixture
def frontend_generator_with_root():
    return FrontendGenerator("test-frontend", False, {"key": "value"}, root="/tmp")


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


def test_frontend_generator_initialization(frontend_generator):
    assert frontend_generator.name == "test-frontend"
    assert frontend_generator.gh is False
    assert frontend_generator.config == {"key": "value"}
    assert frontend_generator.template_dir.name == "react"


def test_frontend_generator_initialization_with_gh(frontend_generator_with_gh):
    assert frontend_generator_with_gh.gh is True


def test_frontend_generator_initialization_with_root(frontend_generator_with_root):
    assert frontend_generator_with_root.project == Path("/tmp/test-frontend")


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


def test_success_message_format(create_mocks):
    generator = FrontendGenerator("my-react-app", False, {})
    generator.create()

    expected_message = "Frontend app 'my-react-app' created successfully in 'my-react-app'!"
    create_mocks.log_success.assert_called_once_with(expected_message)


def test_template_files_count(create_mocks):
    generator = FrontendGenerator("test", False, {})
    generator.create()

    assert create_mocks.write_template.call_count == 15


def test_no_language_specific_logic():
    generator = FrontendGenerator("test", False, {})

    assert not hasattr(generator, "_create_python_structure")
    assert not hasattr(generator, "_create_rust_structure")
    assert not hasattr(generator, "_create_go_structure")
    assert hasattr(generator, "create")


def test_inheritance_from_base_generator():
    from src.generator.base import BaseGenerator

    generator = FrontendGenerator("test", False, {})
    assert isinstance(generator, BaseGenerator)
    assert hasattr(generator, "create_project")
    assert hasattr(generator, "init_basic_structure")
    assert hasattr(generator, "write_template")
    assert hasattr(generator, "create_architecture_docs")
    assert hasattr(generator, "log_success")
