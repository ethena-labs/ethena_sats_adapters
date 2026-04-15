.PHONY: install install-dev lint type-check format

install:
	uv sync

install-dev:
	uv sync --dev

lint:
	uvx ruff check .

type-check:
	uvx ty check .

format:
	uvx ruff format .