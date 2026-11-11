"""Smoke tests for the FlowSpec package scaffold and honest placeholders.

Two groups of modules:

- ``IMPLEMENTED`` — modules with real v0.1.0 implementations; they must
  import cleanly and export their documented symbols.
- ``STUBS`` — modules still awaiting implementation; they must honestly
  raise ``NotImplementedError`` when invoked, never fake success.
"""

from __future__ import annotations

import importlib
import inspect
import subprocess
import sys

import pytest

import flowspec
from flowspec import exceptions

IMPLEMENTED = [
    "flowspec.config",
    "flowspec.parser.yaml_parser",
    "flowspec.parser.json_parser",
    "flowspec.parser.validator",
    "flowspec.parser.ast_builder",
    "flowspec.parser.document",
    "flowspec.ast.nodes",
    "flowspec.ast.expressions",
    "flowspec.ast.workflow",
    "flowspec.ast.visitors",
    "flowspec.diagnostics.models",
    "flowspec.diagnostics.error_codes",
    "flowspec.diagnostics.formatter",
]

STUBS = [
    "flowspec.typesystem.types",
    "flowspec.typesystem.parser",
    "flowspec.typesystem.symbols",
    "flowspec.typesystem.inference",
    "flowspec.typesystem.unification",
    "flowspec.typesystem.type_checker",
    "flowspec.registry.tool_registry",
    "flowspec.registry.schema_loader",
    "flowspec.registry.schema_normalizer",
    "flowspec.semantic.name_resolution",
    "flowspec.semantic.semantic_analyzer",
    "flowspec.graph.graph",
    "flowspec.graph.dependency",
    "flowspec.graph.cycle_detection",
    "flowspec.graph.topological_sort",
    "flowspec.graph.reachability",
    "flowspec.graph.scheduler",
    "flowspec.analysis.static",
    "flowspec.analysis.dataflow",
    "flowspec.analysis.constraints",
    "flowspec.analysis.effects",
    "flowspec.analysis.permissions",
    "flowspec.analysis.suggestions",
    "flowspec.compiler.compiler",
    "flowspec.compiler.pipeline",
    "flowspec.compiler.ir",
    "flowspec.compiler.result",
    "flowspec.execution.planner",
    "flowspec.execution.runtime",
    "flowspec.execution.adapters",
    "flowspec.visualization.graph_renderer",
    "flowspec.visualization.exporters",
]


def _raises_not_implemented(symbol: object) -> bool:
    """Report whether invoking a symbol with dummy arguments refuses fake behavior."""
    for args in ((), (None,), (None, None), (None, None, None)):
        try:
            if inspect.isclass(symbol) or callable(symbol):
                symbol(*args)  # type: ignore[call-arg, operator]
        except NotImplementedError:
            return True
        except TypeError:
            continue
    return False


def test_package_exposes_version() -> None:
    """The package exposes a PEP 440 development version."""
    assert flowspec.__version__ == "0.1.0.dev0"


def test_base_exception_importable() -> None:
    """The structured exception base class is importable."""
    assert issubclass(exceptions.FlowSpecError, Exception)


@pytest.mark.parametrize("module_name", IMPLEMENTED)
def test_implemented_modules_import_cleanly(module_name: str) -> None:
    """Implemented modules import and export public symbols."""
    module = importlib.import_module(module_name)
    public = [name for name in dir(module) if not name.startswith("_")]
    assert public, f"{module_name} exports no public symbols"


@pytest.mark.parametrize("module_name", STUBS)
def test_stub_modules_raise_not_implemented(module_name: str) -> None:
    """Every not-yet-implemented module honestly refuses to fake behavior."""
    module = importlib.import_module(module_name)

    public = [name for name in dir(module) if not name.startswith("_")]
    assert public, f"{module_name} exports no public symbols"

    placeholders = [getattr(module, name) for name in public]
    assert any(_raises_not_implemented(symbol) for symbol in placeholders), (
        f"{module_name} has no placeholder symbol refusing fake behavior"
    )


def test_cli_version_command() -> None:
    """The flowspec CLI runs and reports the package version."""
    result = subprocess.run(
        [sys.executable, "-m", "flowspec.cli", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert f"FlowSpec {flowspec.__version__}" in result.stdout


def test_cli_unimplemented_command_exit_code() -> None:
    """Commands that are not implemented yet fail loudly with exit code 4."""
    result = subprocess.run(
        [sys.executable, "-m", "flowspec.cli", "compile", "nonexistent.yaml"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 4
    assert "not implemented" in result.stderr.lower()
