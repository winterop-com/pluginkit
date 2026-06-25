.PHONY: help install fmt lint test coverage run docs docs-serve docs-build clean

UV := $(shell command -v uv 2> /dev/null)

# Silence the "Material for MkDocs / MkDocs 2.0" announcement banner.
export NO_MKDOCS_2_WARNING := true

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install      Install dependencies"
	@echo "  fmt          Format and autofix (mutates files)"
	@echo "  lint         Check formatting, lints, and types (no mutation)"
	@echo "  test         Run tests"
	@echo "  coverage     Run tests with coverage reporting"
	@echo "  run          Run every demo end to end (DEMO=name for one)"
	@echo "  docs-serve   Serve documentation locally with live reload"
	@echo "  docs-build   Build the documentation site (strict)"
	@echo "  docs         Alias for docs-serve"
	@echo "  clean        Clean up temporary files"

install:
	@echo ">>> Installing dependencies"
	@$(UV) sync --all-extras

fmt:
	@echo ">>> Formatting and autofixing"
	@$(UV) run ruff format .
	@$(UV) run ruff check . --fix

lint:
	@echo ">>> Checking formatting and lints (no mutation)"
	@$(UV) run ruff format --check .
	@$(UV) run ruff check .
	@echo ">>> Running type checkers"
	@$(UV) run mypy src tests examples/cookbook examples/tour/src
	@$(UV) run pyright

test:
	@echo ">>> Running tests"
	@$(UV) run pytest -q

coverage:
	@echo ">>> Running tests with coverage"
	@$(UV) run pytest -q --cov=pluginkit --cov-report=term-missing --cov-report=xml

run:
	@$(UV) run pluginkit-tour run $(or $(DEMO),all)

docs-serve:
	@echo ">>> Serving documentation at http://127.0.0.1:8000"
	@$(UV) run mkdocs serve

docs-build:
	@echo ">>> Building documentation site"
	@$(UV) run mkdocs build --strict

docs: docs-serve

clean:
	@echo ">>> Cleaning up"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov coverage.xml .pyright dist build *.egg-info

.DEFAULT_GOAL := help
