"""Assert every scaffold emits a .github/dependabot.yml that matches its package managers.

Each update entry must point at a directory that really holds the manifest
Dependabot reads for that ecosystem; otherwise Dependabot reports a config
error in the generated repo instead of opening update PRs.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

DEPENDABOT_PATH = ".github/dependabot.yml"

# Manifest globs Dependabot reads per ecosystem, relative to each update directory.
ECOSYSTEM_MANIFESTS = {
    "pip": "pyproject.toml",
    "cargo": "Cargo.toml",
    "bun": "package.json",
    "gomod": "go.mod",
    "docker": "Dockerfile",
    "docker-compose": "docker-compose.yml",
    "terraform": "*.tf",
    "github-actions": ".github/workflows/*.yml",
}

SCAFFOLDS = (
    pytest.param(("service", "--lang", "python"), ["pip", "docker", "github-actions"], id="service-python"),
    pytest.param(("service", "--lang", "rust"), ["cargo", "docker", "github-actions"], id="service-rust"),
    pytest.param(("service", "--lang", "typescript"), ["bun", "docker", "github-actions"], id="service-typescript"),
    pytest.param(("service", "--lang", "go"), ["gomod", "docker", "github-actions"], id="service-go"),
    pytest.param(("service", "--lang", "cpp"), ["docker", "github-actions"], id="service-cpp"),
    pytest.param(
        ("service", "--lang", "typescript", "--runtime", "cloudflare-workers"),
        ["bun", "github-actions"],
        id="service-typescript-cf",
    ),
    pytest.param(
        ("service", "--lang", "rust", "--runtime", "cloudflare-workers"),
        ["cargo", "bun", "github-actions"],
        id="service-rust-cf",
    ),
    pytest.param(("cli", "--lang", "python"), ["pip", "github-actions"], id="cli-python"),
    pytest.param(("cli", "--lang", "rust"), ["cargo", "github-actions"], id="cli-rust"),
    pytest.param(("cli", "--lang", "typescript"), ["bun", "github-actions"], id="cli-typescript"),
    pytest.param(("lib", "--lang", "python"), ["pip", "github-actions"], id="lib-python"),
    pytest.param(("lib", "--lang", "rust"), ["cargo", "github-actions"], id="lib-rust"),
    pytest.param(("frontend",), ["bun", "docker", "github-actions"], id="frontend"),
    pytest.param(("system",), ["terraform", "docker-compose", "github-actions"], id="system"),
    pytest.param(
        ("system", "--workspace-tooling", "bun-turbo"),
        ["bun", "terraform", "docker-compose", "github-actions"],
        id="system-bun-turbo",
    ),
    pytest.param(("system", "--cloud", "none"), ["docker-compose", "github-actions"], id="system-no-cloud"),
)


@pytest.mark.parametrize(("create_args", "ecosystems"), SCAFFOLDS)
def test_scaffold_emits_dependabot_config(
    kickstart_run, tmp_path: Path, create_args: tuple[str, ...], ecosystems: list[str]
) -> None:
    kind, *options = create_args
    completed = kickstart_run(
        "create", kind, "dependabot-demo", *options, "--root", str(tmp_path), capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    project = tmp_path / "dependabot-demo"

    config = yaml.safe_load((project / DEPENDABOT_PATH).read_text())

    assert config["version"] == 2
    assert [update["package-ecosystem"] for update in config["updates"]] == ecosystems
    for update in config["updates"]:
        ecosystem = update["package-ecosystem"]
        for directory in update.get("directories") or [update["directory"]]:
            manifests = list(project.glob(f"{directory.lstrip('/')}/{ECOSYSTEM_MANIFESTS[ecosystem]}".lstrip("/")))
            assert manifests, f"{ecosystem} points at {directory}, which has no {ECOSYSTEM_MANIFESTS[ecosystem]}"
