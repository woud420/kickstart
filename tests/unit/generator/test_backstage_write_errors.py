"""Catalog write failures remain visible across exporter error translation."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.generator.backstage_export import CATALOG_PATH, BackstageExportError, export_backstage
from src.generator.scaffold_contract import MANIFEST_PATH, ScaffoldContract


def test_catalog_write_failure_preserves_repo(tmp_path: Path) -> None:
    contract = ScaffoldContract(
        schema_version="3.2",
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
    )
    (tmp_path / ".kickstart").mkdir()
    (tmp_path / MANIFEST_PATH).write_text(contract.manifest_json("demo"), encoding="utf-8")
    (tmp_path / "README.md").write_text("User-owned notes\n", encoding="utf-8")
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    with patch.object(Path, "write_text", autospec=True, side_effect=OSError("diskfull")) as write:
        with pytest.raises((OSError, BackstageExportError)) as caught:
            export_backstage(tmp_path)

    assert str(caught.value) in ("diskfull", "cannot write catalog-info.yaml: diskfull")
    write.assert_called_once()
    assert write.call_args.args[0] == tmp_path / CATALOG_PATH
    assert not (tmp_path / CATALOG_PATH).exists()
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before
