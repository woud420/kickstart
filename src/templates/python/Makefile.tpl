.PHONY: install test lint typecheck

install:
	poetry install

test:
	poetry run pytest

lint:
	poetry run ruff check .

typecheck:
	poetry run mypy src
