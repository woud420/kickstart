[package]
name = "{{ package_name }}"
version = "0.2.1"
edition = "2024"

[dependencies]
actix-web = "4"
{% if cache == "redis" %}
redis = { version = "1.2", features = ["tokio-comp"] }
{% endif %}
