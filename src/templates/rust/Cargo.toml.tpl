[package]
name = "{{ package_name }}"
version = "0.1.0"
edition = "2024"

[dependencies]
actix-web = "4"
# actix-web 4 depends on cookie 0.16, which fails to compile against
# time >= 0.3.48. Drop this pin once actix-web moves to cookie >= 0.17.
time = ">=0.3, <0.3.48"
{% if cache == "redis" %}
redis = { version = "1.2", features = ["tokio-comp"] }
{% endif %}
{% if auth == "jwt" %}
jsonwebtoken = "9"
serde = { version = "1", features = ["derive"] }
{% endif %}
