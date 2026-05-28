"""Single source of truth for toolchain version pins rendered into scaffolds.

Each constant is consumed by Jinja templates via the ``vars`` field of a
``TemplateConfig``. Keeping the pins here means a generated project's
Dockerfile, package manifest, and CI workflow agree on a single version
without having to chase string literals across templates.
"""

from typing import Final

from src.utils.types import TemplateValue

BUN_VERSION: Final[str] = "1.3.0"
PYTHON_DOCKER_TAG: Final[str] = "3.12-slim-bookworm"
PYTHON_MATRIX: Final[tuple[str, ...]] = ("3.12", "3.13", "3.14")
RUST_TOOLCHAIN: Final[str] = "1.85"
RUST_DOCKER_TAG: Final[str] = "1.85-bookworm"
GO_VERSION: Final[str] = "1.26"


def toolchain_vars() -> dict[str, TemplateValue]:
    """Return all toolchain version pins as a flat dict for template rendering.

    Templates pick up only the keys they reference; unused keys are ignored
    by Jinja.
    """
    return {
        "bun_version": BUN_VERSION,
        "python_docker_tag": PYTHON_DOCKER_TAG,
        "python_matrix": list(PYTHON_MATRIX),
        "rust_toolchain": RUST_TOOLCHAIN,
        "rust_docker_tag": RUST_DOCKER_TAG,
        "go_version": GO_VERSION,
    }
