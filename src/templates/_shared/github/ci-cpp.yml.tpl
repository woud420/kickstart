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

      - name: Install build tooling
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends build-essential cmake

      - run: make check
