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
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ "{{" }} matrix.python-version {{ "}}" }}

      - name: Install Poetry
        run: pipx install poetry

      - name: Cache poetry virtualenv
        uses: actions/cache@v4
        with:
          path: |
            .cache
            .venv
          key: ${{ "{{" }} runner.os {{ "}}" }}-poetry-${{ "{{" }} matrix.python-version {{ "}}" }}-${{ "{{" }} hashFiles('poetry.lock', 'pyproject.toml') {{ "}}" }}

      - run: make check
