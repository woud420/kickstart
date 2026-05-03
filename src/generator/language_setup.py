"""Static language setup plans for service generators."""

from collections.abc import Sequence

from src.generator.file_plan import ContentFile
from src.stack.types import TemplateConfig
from src.utils.types import TemplateVars


RUST_MODULE_CONTENT = "// Module definitions\n"
RUST_CLIENTS_MODULE_CONTENT = "pub mod cache;\n"
RUST_HANDLER_MODULE_CONTENT = "pub mod auth;\n"

RUST_MAIN_CONTENT = """use actix_web::{App, HttpResponse, HttpServer, web};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new().route(
            "/",
            web::get().to(|| async { HttpResponse::Ok().json("Hello World") }),
        )
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
"""

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

GO_MAIN_CONTENT = """package main

import (
    "fmt"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, `{"message": "Hello World"}`)
    })
    fmt.Println("Listening on :8080...")
    http.ListenAndServe(":8080", nil)
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


def rust_service_content_files(
    *,
    include_redis_cache: bool = False,
    include_jwt_auth: bool = False,
) -> tuple[ContentFile, ...]:
    """Return direct content files for Rust services."""
    module_lines = []
    if include_redis_cache:
        module_lines.append("mod clients;")
    if include_jwt_auth:
        module_lines.append("mod handler;")
    main_content = RUST_MAIN_CONTENT
    if module_lines:
        main_content = "\n".join(module_lines) + f"\n\n{RUST_MAIN_CONTENT}"

    files: tuple[ContentFile, ...] = (
        ContentFile("src/api/mod.rs", RUST_MODULE_CONTENT),
        ContentFile("src/model/mod.rs", RUST_MODULE_CONTENT),
        ContentFile("tests/api/mod.rs", RUST_MODULE_CONTENT),
        ContentFile("tests/model/mod.rs", RUST_MODULE_CONTENT),
        ContentFile("src/main.rs", main_content),
    )
    if include_redis_cache:
        files = (*files, ContentFile("src/clients/mod.rs", RUST_CLIENTS_MODULE_CONTENT))
    if include_jwt_auth:
        files = (*files, ContentFile("src/handler/mod.rs", RUST_HANDLER_MODULE_CONTENT))
    return files


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
        ContentFile("src/main.go", GO_MAIN_CONTENT),
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
