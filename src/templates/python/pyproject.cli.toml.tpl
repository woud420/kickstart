[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "{{ package_name }}"
version = "0.1.0"
description = "{{ service_name }} Python CLI"
authors = ["You"]
packages = [{ include = "src" }]

[tool.poetry.dependencies]
python = ">=3.12,<3.15"
typer = ">=0.20,<1"
rich = ">=14,<15"

[tool.poetry.scripts]
{{ package_name | replace("-", "_") }} = "src.main:main"

[tool.poetry.group.dev.dependencies]
pytest = ">=8.4,<9"
ruff = ">=0.14,<1"
mypy = ">=1.20,<2"

[tool.mypy]
python_version = "3.12"
strict = true

[[tool.mypy.overrides]]
module = ["asyncpg", "jose.*", "passlib.*"]
ignore_missing_imports = true

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["B", "N", "UP"]

[tool.pytest.ini_options]
addopts = "-ra --strict-markers --strict-config"
testpaths = ["tests"]
markers = [
    "unit: fast, isolated tests",
    "integration: tests that touch external services",
    "slow: long-running tests",
]
