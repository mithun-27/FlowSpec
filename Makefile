# FlowSpec development tasks.
#
# NOTE (Windows): GNU Make is not available by default on Windows. Run the
# underlying `python -m ...` commands directly in PowerShell instead — see
# docs/contributing.md for the exact commands.

.PHONY: install dev lint format typecheck test test-cov build clean

install: ## Install the package into the active environment
	python -m pip install -e .

dev: ## Install the package with development dependencies
	python -m pip install -e ".[dev]"

lint: ## Run Ruff lint and format checks
	python -m ruff check src tests
	python -m ruff format --check src tests

format: ## Apply Ruff formatting
	python -m ruff format src tests

typecheck: ## Run Mypy on the package source
	python -m mypy src

test: ## Run the test suite
	python -m pytest

test-cov: ## Run the test suite with coverage reporting
	python -m pytest --cov=flowspec --cov-report=term-missing

build: ## Build sdist and wheel distributions
	python -m build

clean: ## Remove build artifacts and tool caches
	rm -rf dist build .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf src/flowspec.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
