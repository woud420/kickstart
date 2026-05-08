[package]
name = "{{ package_name }}"
version = "0.1.0"
edition = "2024"

[dependencies]
clap = { version = "4.5", features = ["derive"] }

[dev-dependencies]
assert_cmd = "2.1"
