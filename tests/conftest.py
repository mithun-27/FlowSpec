"""Shared pytest fixtures for the FlowSpec test suite.

Status: scaffolding — fixtures are added together with the compiler
features they exercise.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def examples_dir() -> Path:
    """Path to the repository's examples directory."""
    return REPO_ROOT / "examples"


@pytest.fixture
def invoice_example_dir(examples_dir: Path) -> Path:
    """Path to the invoice_processing example project."""
    return examples_dir / "invoice_processing"
