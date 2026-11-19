import json
from pathlib import Path
import tomllib

import pytest

from src.stack.toolchain_versions import RUST_TOOLCHAIN, TYPESCRIPT_COMPAT_VERSION, TYPESCRIPT_VERSION


@pytest.mark.parametrize(
    ("kind", "options"),
    [
        ("service", ("--lang", "typescript")),
        ("service", ("--lang", "typescript", "--runtime", "cloudflare-workers")),
        ("cli", ("--lang", "typescript")),
        ("frontend", ()),
        ("system", ("--workspace-tooling", "bun-turbo")),
    ],
)
def test_typescript_compiler_pin(kickstart_run, tmp_path: Path, kind: str, options: tuple[str, ...]) -> None:
    kickstart_run("create", kind, "sample", *options, "--root", str(tmp_path), check=True)
    deps = json.loads((tmp_path / "sample/package.json").read_text())["devDependencies"]
    if kind == "system":
        assert deps["typescript"] == TYPESCRIPT_VERSION
    else:
        assert deps["@typescript/native"] == f"npm:typescript@{TYPESCRIPT_VERSION}"
        assert deps["typescript"] == f"npm:@typescript/typescript6@{TYPESCRIPT_COMPAT_VERSION}"


@pytest.mark.parametrize(
    ("kind", "options"),
    [("service", ()), ("service", ("--runtime", "cloudflare-workers")), ("cli", ()), ("lib", ())],
)
def test_rust_toolchain_agrees_across_outputs(
    kickstart_run, tmp_path: Path, kind: str, options: tuple[str, ...]
) -> None:
    kickstart_run("create", kind, "sample", "--lang", "rust", *options, "--root", str(tmp_path), check=True)
    project = tmp_path / "sample"
    assert tomllib.loads((project / "Cargo.toml").read_text())["package"]["rust-version"] == RUST_TOOLCHAIN
    assert tomllib.loads((project / "rust-toolchain.toml").read_text())["toolchain"]["channel"] == RUST_TOOLCHAIN
    assert f'toolchain: "{RUST_TOOLCHAIN}"' in (project / ".github/workflows/ci.yml").read_text()
    if kind == "service" and not options:
        assert f"FROM rust:{RUST_TOOLCHAIN}-bookworm AS builder" in (project / "Dockerfile").read_text()
