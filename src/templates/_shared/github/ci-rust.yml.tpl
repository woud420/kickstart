name: CI

on:
  pull_request:
    branches: [main, master]
  push:
    branches: [main, master]

permissions:
  contents: read

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable
        with:
          toolchain: "{{ rust_toolchain }}"
          components: rustfmt, clippy

      - uses: Swatinem/rust-cache@v2

      - run: make check
