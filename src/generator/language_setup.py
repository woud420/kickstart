"""Static language setup plans for service generators."""

from dataclasses import dataclass

from src.stack.types import TemplateConfig


@dataclass(frozen=True)
class ContentFile:
    """Direct file content to write during language setup."""

    target: str
    content: str


RUST_MODULE_CONTENT = "// Module definitions\n"

RUST_MAIN_CONTENT = """use actix_web::{web, App, HttpResponse, HttpServer};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/", web::get().to(|| async { HttpResponse::Ok().json("Hello World") }))
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


def rust_service_content_files() -> tuple[ContentFile, ...]:
    """Return direct content files for Rust services."""
    return (
        ContentFile("src/api/mod.rs", RUST_MODULE_CONTENT),
        ContentFile("src/model/mod.rs", RUST_MODULE_CONTENT),
        ContentFile("tests/api/mod.rs", RUST_MODULE_CONTENT),
        ContentFile("tests/model/mod.rs", RUST_MODULE_CONTENT),
        ContentFile("src/main.rs", RUST_MAIN_CONTENT),
    )


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


def typescript_service_templates() -> tuple[TemplateConfig, ...]:
    """Return template files for TypeScript services."""
    return (
        TemplateConfig("src/main.ts", "typescript/src/main.ts.tpl"),
        TemplateConfig("src/config/env.ts", "typescript/src/config/env.ts.tpl"),
        TemplateConfig("src/routes/health.ts", "typescript/src/routes/health.ts.tpl"),
        TemplateConfig("tests/health.test.ts", "typescript/tests/health.test.ts.tpl"),
    )


def typescript_service_content_files() -> tuple[ContentFile, ...]:
    """Return direct content files for TypeScript services."""
    return (ContentFile(".env.example", TYPESCRIPT_ENV_EXAMPLE_CONTENT),)
