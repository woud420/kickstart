[package]
name = "{{ package_name }}"
version = "0.1.0"
edition = "2024"

[dependencies]
actix-web = "4"
{% if cache == "redis" %}
redis = { version = "1.2", features = ["tokio-comp"] }
{% endif %}
{% if auth == "jwt" %}
jsonwebtoken = "9"
serde = { version = "1", features = ["derive"] }
{% endif %}
