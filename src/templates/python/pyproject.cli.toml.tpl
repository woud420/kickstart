[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "{{ service_name }}"
version = "0.1.0"
description = "{{ service_name }} Python CLI"
authors = ["You"]
packages = [{ include = "src" }]

[tool.poetry.dependencies]
python = "^3.12"
typer = "^0.12.0"
rich = "^13.0.0"

[tool.poetry.scripts]
{{ service_name | replace("-", "_") }} = "src.main:main"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
ruff = "^0.6.0"
mypy = "^1.11.0"

[tool.mypy]
python_version = "3.12"
strict = true

[tool.ruff]
line-length = 100
target-version = "py312"
