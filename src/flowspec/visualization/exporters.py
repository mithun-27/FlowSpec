"""Exporters for FlowSpec artifacts.

Serializes compilation results and their intermediate representations as
deterministic JSON: sorted keys, no timestamps, values derived only from
the compiled sources. Identical inputs and configuration always produce
identical output.

Only JSON is exported in v0.1.0. Other machine-readable formats (and
graph rendering) are planned for later releases; see
``docs/PROGRESS.md``.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

import json

from flowspec.compiler.result import CompilationResult

__all__ = ["export_ir", "export_result"]


def export_ir(result: CompilationResult, indent: int = 2) -> str:
    """Render a compilation result's IR as deterministic JSON.

    Raises:
        ValueError: the compilation produced no IR (the workflow did not
            compile cleanly, or IR generation is disabled). Invalid
            workflows are never exported as executable IR.
    """
    if result.ir is None:
        raise ValueError(
            "the compilation produced no IR; use export_result() for the "
            "diagnostics of a failed compilation"
        )
    return result.ir.to_json(indent=indent)


def export_result(result: CompilationResult, indent: int = 2) -> str:
    """Render a full compilation result as deterministic JSON.

    Includes the outcome, the workflow name, a summary, every diagnostic,
    and the IR when one was generated.
    """
    return json.dumps(result.to_dict(), indent=indent, sort_keys=True)
