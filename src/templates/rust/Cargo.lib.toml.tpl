[package]
name = "{{ package_name }}"
version = "0.1.0"
rust-version = "{{ rust_toolchain }}"
edition = "2024"

[lib]
path = "src/lib.rs"

[dependencies]
