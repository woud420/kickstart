import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.embed_posthog_token import render_build_config
from scripts.verify_embedded_telemetry_artifact import embedded_token_from_artifact, verify_artifact


def test_verify_wheel_with_embedded_token(tmp_path: Path) -> None:
    artifact = tmp_path / "kickstart-test.whl"
    with zipfile.ZipFile(artifact, mode="w") as archive:
        archive.writestr("src/telemetry/_build_config.py", render_build_config("phc_wheel_test_token"))

    verify_artifact(artifact)

    assert embedded_token_from_artifact(artifact) == "phc_wheel_test_token"


def test_verify_sdist_with_embedded_token(tmp_path: Path) -> None:
    artifact = tmp_path / "kickstart-test.tar.gz"
    content = render_build_config("phc_sdist_test_token").encode()
    member = tarfile.TarInfo("kickstart-test/src/telemetry/_build_config.py")
    member.size = len(content)
    with tarfile.open(artifact, mode="w:gz") as archive:
        archive.addfile(member, io.BytesIO(content))

    verify_artifact(artifact)


def test_verify_rejects_empty_placeholder(tmp_path: Path) -> None:
    artifact = tmp_path / "kickstart-test.whl"
    with zipfile.ZipFile(artifact, mode="w") as archive:
        archive.writestr(
            "src/telemetry/_build_config.py", render_build_config("phc_fixture").replace("phc_fixture", "")
        )

    with pytest.raises(ValueError, match="does not contain"):
        verify_artifact(artifact)


def test_verify_rejects_a_token_from_another_posthog_project(tmp_path: Path) -> None:
    artifact = tmp_path / "kickstart-test.whl"
    with zipfile.ZipFile(artifact, mode="w") as archive:
        archive.writestr("src/telemetry/_build_config.py", render_build_config("phc_wrong_project_token"))

    with pytest.raises(ValueError, match="configured PostHog project"):
        verify_artifact(artifact, expected_project_token="phc_expected_project_token")
