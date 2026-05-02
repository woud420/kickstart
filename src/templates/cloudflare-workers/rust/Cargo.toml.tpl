[package]
name = "{{ service_name }}"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
console_error_panic_hook = "0.1"
serde_json = "1"
worker = "0.8"

[profile.release]
codegen-units = 1
lto = true
strip = true
