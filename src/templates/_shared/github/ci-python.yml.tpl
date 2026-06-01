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
        python-version: {{ python_matrix | tojson }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ "{{" }} matrix.python-version {{ "}}" }}

      - name: Install Poetry
        run: pipx install "poetry=={{ poetry_version }}"

      - name: Cache poetry virtualenv
        uses: actions/cache@v4
        with:
          path: |
            .cache
            .venv
          key: ${{ "{{" }} runner.os {{ "}}" }}-poetry-{{ poetry_version }}-${{ "{{" }} matrix.python-version {{ "}}" }}-${{ "{{" }} hashFiles('poetry.lock', 'pyproject.toml') {{ "}}" }}

      - run: make check
