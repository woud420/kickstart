"""Single source of truth for toolchain version pins rendered into scaffolds.

Each constant is consumed by Jinja templates via the ``vars`` field of a
``TemplateConfig``. Keeping the pins here means a generated project's
Dockerfile, package manifest, and CI workflow agree on a single version
without having to chase string literals across templates.

Scope: language toolchains only. Base images that are not language
toolchains (cpp's ``gcc:14`` builder, react's ``nginx:1.27-alpine``
runtime) stay pinned in their templates deliberately — nothing else in
those scaffolds has to agree with them, so there is no cross-file drift
for this module to prevent.
"""

from typing import Final

from src.utils.types import TemplateValue

BUN_VERSION: Final[str] = "1.3.0"
PYTHON_DOCKER_TAG: Final[str] = "3.12-slim-bookworm"
PYTHON_MATRIX: Final[tuple[str, ...]] = ("3.12", "3.13", "3.14")
POETRY_VERSION: Final[str] = "1.8.4"
RUST_TOOLCHAIN: Final[str] = "1.88"
RUST_DOCKER_TAG: Final[str] = "1.88-bookworm"
GO_VERSION: Final[str] = "1.26"
# Must provide at least GO_VERSION: generated go.mod requires >= GO_VERSION
# and the builder runs with GOTOOLCHAIN defaulting to local, so a builder
# image older than go.mod breaks every generated Go service container.
GO_DOCKER_TAG: Final[str] = "1.26.2-bookworm"


def toolchain_vars() -> dict[str, TemplateValue]:
    """Return all toolchain version pins as a flat dict for template rendering.

    Templates pick up only the keys they reference; unused keys are ignored
    by Jinja.
    """
    return {
        "bun_version": BUN_VERSION,
        "python_docker_tag": PYTHON_DOCKER_TAG,
        "python_matrix": list(PYTHON_MATRIX),
        "poetry_version": POETRY_VERSION,
        "rust_toolchain": RUST_TOOLCHAIN,
        "rust_docker_tag": RUST_DOCKER_TAG,
        "go_version": GO_VERSION,
        "go_docker_tag": GO_DOCKER_TAG,
    }
