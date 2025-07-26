[package]
name = "{{SERVICE_NAME}}"
version = "0.1.0"
edition = "2021"
description = "{{SERVICE_NAME}} - A Rust service"

[dependencies]
actix-web = "4.9"
tokio = { version = "1.0", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
env_logger = "0.11"
log = "0.4"
anyhow = "1.0"

[dev-dependencies]
actix-rt = "2.9"
