"""A write that fails during setup must fail creation, even when setup ignores it."""

from collections.abc import Callable
from unittest.mock import Mock

import pytest

from src.generator import base
from src.generator.base import BaseGenerator
from src.generator.lib import CLIGenerator, LibraryGenerator
from src.generator.monorepo import SystemGenerator
from src.generator.service import ServiceGenerator
from src.utils.errors import ProjectCreationError


def _fail_writes_during(generator: BaseGenerator, setup_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every file write inside one setup method raise OSError."""
    failing = False
    real_write_file = base.write_file

    def write_file(*args: object, **kwargs: object) -> None:
        if failing:
            raise OSError("disk full")
        real_write_file(*args, **kwargs)

    setup = getattr(generator, setup_name)

    def failing_setup() -> bool:
        nonlocal failing
        failing = True
        try:
            return setup()
        finally:
            failing = False

    monkeypatch.setattr(base, "write_file", write_file)
    monkeypatch.setattr(generator, setup_name, failing_setup)


CASES: list[tuple[str, Callable[[str], BaseGenerator], str, str]] = [
    ("library-python", lambda root: LibraryGenerator("lib-py", "python", True, {}, root=root),
     "_setup_language_specific_files", "src.generator.lib.create_repo"),
    ("library-rust", lambda root: LibraryGenerator("lib-rs", "rust", True, {}, root=root),
     "_setup_language_specific_files", "src.generator.lib.create_repo"),
    ("cli-python", lambda root: CLIGenerator("cli-py", "python", True, {}, root=root),
     "_setup_cli_specific_files", "src.generator.lib.create_repo"),
    *[
        (f"service-{lang}", lambda root, lang=lang: ServiceGenerator(f"svc-{lang}", lang, True, {}, root=root),
         "_setup_service_specific", "src.generator.service.create_repo")
        for lang in ("python", "rust", "go", "cpp", "typescript")
    ],
    ("system", lambda root: SystemGenerator("sys", True, {}, root=root),
     "_setup_system_specific", "src.generator.monorepo.create_repo"),
]


@pytest.mark.parametrize(("case", "make", "setup_name", "create_repo_path"), CASES, ids=[c[0] for c in CASES])
def test_failed_setup_write_blocks_success_and_remote(tmp_path, monkeypatch, case, make, setup_name, create_repo_path):
    generator = make(str(tmp_path))
    create_repo = Mock(return_value=True)
    banner = Mock()
    monkeypatch.setattr(create_repo_path, create_repo)
    monkeypatch.setattr(generator, "log_success", banner)
    _fail_writes_during(generator, setup_name, monkeypatch)

    with pytest.raises(ProjectCreationError, match="could not write"):
        generator.create()

    banner.assert_not_called()
    create_repo.assert_not_called()
