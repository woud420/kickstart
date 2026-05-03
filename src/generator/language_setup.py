"""Static language setup plans for service generators."""

from dataclasses import dataclass

from src.stack.types import TemplateConfig


@dataclass(frozen=True)
class ContentFile:
    """Direct file content to write during language setup."""

    target: str
    content: str


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

TYPESCRIPT_POSTGRES_ENV_LINE = "DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/postgres\n"
TYPESCRIPT_REDIS_ENV_LINE = "REDIS_URL=redis://127.0.0.1:6379/0\n"


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


def typescript_service_templates(
    *,
    include_postgres_database: bool = False,
    include_redis_cache: bool = False,
) -> tuple[TemplateConfig, ...]:
    """Return template files for TypeScript services."""
    template_vars: dict[str, str] = {}
    if include_postgres_database:
        template_vars["database"] = "postgres"
    if include_redis_cache:
        template_vars["cache"] = "redis"
    return (
        TemplateConfig("src/main.ts", "typescript/src/main.ts.tpl", template_vars),
        TemplateConfig("src/config/env.ts", "typescript/src/config/env.ts.tpl", template_vars),
        TemplateConfig("src/routes/health.ts", "typescript/src/routes/health.ts.tpl", template_vars),
        TemplateConfig("tests/health.test.ts", "typescript/tests/health.test.ts.tpl", template_vars),
    )


def typescript_service_content_files(
    *,
    include_postgres_database: bool = False,
    include_redis_cache: bool = False,
) -> tuple[ContentFile, ...]:
    """Return direct content files for TypeScript services."""
    env_content = TYPESCRIPT_ENV_EXAMPLE_CONTENT
    if include_postgres_database:
        env_content += TYPESCRIPT_POSTGRES_ENV_LINE
    if include_redis_cache:
        env_content += TYPESCRIPT_REDIS_ENV_LINE
    return (ContentFile(".env.example", env_content),)
