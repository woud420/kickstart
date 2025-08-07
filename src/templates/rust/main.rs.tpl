use actix_web::{web, App, HttpResponse, HttpServer, Result, middleware::Logger};
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    service: String,
    version: String,
}

#[derive(Serialize)]
struct RootResponse {
    message: String,
}

async fn root() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json(RootResponse {
        message: "{{SERVICE_NAME}} is running".to_string(),
    }))
}

async fn health() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json(HealthResponse {
        status: "healthy".to_string(),
        service: "{{SERVICE_NAME}}".to_string(),
        version: "0.1.0".to_string(),
    }))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();

    let host = env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = env::var("PORT").unwrap_or_else(|_| "8000".to_string());
    let bind_address = format!("{}:{}", host, port);

    log::info!("Starting {{SERVICE_NAME}} server on {}", bind_address);

    HttpServer::new(|| {
        App::new()
            .wrap(Logger::default())
            .route("/", web::get().to(root))
            .route("/health", web::get().to(health))
    })
    .bind(&bind_address)?
    .run()
    .await
}
