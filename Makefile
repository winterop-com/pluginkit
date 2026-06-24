.PHONY: help install lint test run bench docs docs-serve docs-build clean

UV := $(shell command -v uv 2> /dev/null)

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install      Install dependencies"
	@echo "  lint         Run linter and type checkers"
	@echo "  test         Run tests"
	@echo "  run          Run every demo end to end (DEMO=name for one)"
	@echo "  bench        Benchmark pluginkit against pluggy"
	@echo "  docs-serve   Serve documentation locally with live reload"
	@echo "  docs-build   Build the documentation site (strict)"
	@echo "  docs         Alias for docs-serve"
	@echo "  clean        Clean up temporary files"

install:
	@echo ">>> Installing dependencies"
	@$(UV) sync --all-extras

lint:
	@echo ">>> Running linter"
	@$(UV) run ruff format .
	@$(UV) run ruff check . --fix
	@echo ">>> Running type checkers"
	@$(UV) run mypy src tests examples tour/src
	@$(UV) run pyright

test:
	@echo ">>> Running tests"
	@$(UV) run pytest -q

run:
	@$(UV) run pluginkit-tour run $(or $(DEMO),all)

bench:
	@$(UV) run python benchmarks/bench.py

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
