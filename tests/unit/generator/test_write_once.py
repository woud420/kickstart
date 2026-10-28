"""Each generated file is rendered once; a second write must be an explicit replace."""

from pathlib import Path

import pytest

from src.generator.base import BaseGenerator
from src.generator.service import ServiceGenerator


@pytest.fixture
def generator(tmp_path: Path) -> BaseGenerator:
    return BaseGenerator("write-once", {}, root=str(tmp_path))


def test_second_write_to_same_path_is_refused(generator: BaseGenerator) -> None:
    assert generator.write_content("notes.txt", "first\n") is True
    assert generator.write_content("notes.txt", "second\n") is False

    assert (generator.project / "notes.txt").read_text() == "first\n"
    assert generator._failed_writes == ["notes.txt (already written)"]


def test_template_rewrite_is_refused_like_content(generator: BaseGenerator) -> None:
    assert generator.write_content("README.md", "seed\n") is True
    assert generator.write_template("README.md", "python/README.md.tpl") is False
    assert generator._failed_writes == ["README.md (already written)"]


def test_replace_allows_a_deliberate_rewrite(generator: BaseGenerator) -> None:
    generator.write_content("notes.txt", "first\n")

    assert generator.write_content("notes.txt", "second\n", replace=True) is True
    assert (generator.project / "notes.txt").read_text() == "second\n"
    assert generator._failed_writes == []


def test_typescript_jwt_readme_renders_from_profile_with_auth_vars() -> None:
    generator = ServiceGenerator("svc", "typescript", False, {}, database="postgres", auth="jwt")

    assert generator._profile_extension_vars() == {
        "package.json": {"auth": "jwt", "database": "postgres"},
        "README.md": {"database": "postgres", "auth": "jwt"},
    }


def test_python_requirements_written_once_with_extension_lines(tmp_path: Path) -> None:
    ServiceGenerator("svc", "python", False, {}, root=str(tmp_path), database="postgres", cache="redis").create()

    requirements = (tmp_path / "svc" / "requirements.txt").read_text()
    assert requirements.count("# Extension requirements") == 1
    assert "fastapi" in requirements
    assert "asyncpg" in requirements and "redis" in requirements
