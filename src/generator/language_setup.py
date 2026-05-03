"""Static language setup plans for service generators."""

from collections.abc import Sequence

from src.generator.file_plan import ContentFile
from src.stack.types import TemplateConfig
from src.utils.types import TemplateVars


CPP_ROUTES_HEADER_CONTENT = """#pragma once

namespace api {
class Routes {
public:
    Routes() = default;
};
}  // namespace api
"""

CPP_USER_HEADER_CONTENT = """#pragma once

#include <string>

namespace model {
struct User {
    std::string id;
    std::string email;
};
}  // namespace model
"""

CPP_MAIN_CONTENT = """#include <iostream>

int main() {
    std::cout << "Hello World" << std::endl;
    return 0;
}
"""

TYPESCRIPT_ENV_EXAMPLE_CONTENT = """HOST=0.0.0.0
PORT=8080
LOG_LEVEL=info
"""

TYPESCRIPT_POSTGRES_ENV_EXAMPLE_CONTENT = (
    f"{TYPESCRIPT_ENV_EXAMPLE_CONTENT}DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/postgres\n"
)
PYTHON_SMOKE_TEST_CONTENT = "def test_generated_scaffold() -> None:\n    assert True\n"


def python_init_content_files(package_paths: Sequence[str]) -> tuple[ContentFile, ...]:
    """Return Python package marker files for generated package directories."""
    return tuple(ContentFile(f"{package_path}/__init__.py", "") for package_path in package_paths)


def python_service_content_files(*, env_content: str, migration_content: str) -> tuple[ContentFile, ...]:
    """Return direct content files for Python services."""
    return (
        ContentFile(".env.example", env_content),
        ContentFile("migrations/001_initial.sql", migration_content),
        ContentFile("tests/test_smoke.py", PYTHON_SMOKE_TEST_CONTENT),
    )


def rust_service_content_templates(
    *,
    include_redis_cache: bool = False,
    include_jwt_auth: bool = False,
) -> tuple[TemplateConfig, ...]:
    """Return source templates written as direct content for Rust services."""
    templates: tuple[TemplateConfig, ...] = (
        TemplateConfig("src/api/mod.rs", "rust/src/api/mod.rs.tpl"),
        TemplateConfig("src/model/mod.rs", "rust/src/model/mod.rs.tpl"),
        TemplateConfig("tests/api/mod.rs", "rust/tests/api/mod.rs.tpl"),
        TemplateConfig("tests/model/mod.rs", "rust/tests/model/mod.rs.tpl"),
        TemplateConfig(
            "src/main.rs",
            "rust/src/main.rs.tpl",
            {
                "include_redis_cache": include_redis_cache,
                "include_jwt_auth": include_jwt_auth,
            },
        ),
    )
    if include_redis_cache:
        templates = (*templates, TemplateConfig("src/clients/mod.rs", "rust/src/clients/mod.rs.tpl"))
    if include_jwt_auth:
        templates = (*templates, TemplateConfig("src/handler/mod.rs", "rust/src/handler/mod.rs.tpl"))
    return templates


def cpp_service_content_files() -> tuple[ContentFile, ...]:
    """Return direct content files for C++ services."""
    return (
        ContentFile("src/api/routes.hpp", CPP_ROUTES_HEADER_CONTENT),
        ContentFile("src/model/user.hpp", CPP_USER_HEADER_CONTENT),
        ContentFile("src/main.cpp", CPP_MAIN_CONTENT),
    )


def go_service_content_files() -> tuple[ContentFile, ...]:
    """Return direct content files for Go services."""
    return (
        ContentFile("src/api/.gitkeep", ""),
        ContentFile("src/model/.gitkeep", ""),
        ContentFile("tests/api/.gitkeep", ""),
        ContentFile("tests/model/.gitkeep", ""),
    )


def go_service_content_templates() -> tuple[TemplateConfig, ...]:
    """Return source templates written as direct content for Go services."""
    return (
        TemplateConfig("src/main.go", "go/src/main.go.tpl"),
        TemplateConfig("src/api/health.go", "go/src/api/health.go.tpl"),
        TemplateConfig("src/model/user.go", "go/src/model/user.go.tpl"),
        TemplateConfig("tests/api/health_test.go", "go/tests/api/health_test.go.tpl"),
    )


def typescript_service_templates(*, include_postgres_database: bool = False) -> tuple[TemplateConfig, ...]:
    """Return template files for TypeScript services."""
    template_vars: TemplateVars = {"database": "postgres"} if include_postgres_database else {}
    return (
        TemplateConfig("src/main.ts", "typescript/src/main.ts.tpl", template_vars),
        TemplateConfig("src/config/env.ts", "typescript/src/config/env.ts.tpl", template_vars),
        TemplateConfig("src/routes/health.ts", "typescript/src/routes/health.ts.tpl", template_vars),
        TemplateConfig("tests/health.test.ts", "typescript/tests/health.test.ts.tpl", template_vars),
    )


def typescript_service_content_files(*, include_postgres_database: bool = False) -> tuple[ContentFile, ...]:
    """Return direct content files for TypeScript services."""
    env_content = TYPESCRIPT_POSTGRES_ENV_EXAMPLE_CONTENT if include_postgres_database else TYPESCRIPT_ENV_EXAMPLE_CONTENT
    return (ContentFile(".env.example", env_content),)
