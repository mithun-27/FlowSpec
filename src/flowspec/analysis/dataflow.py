"""Dataflow analysis.

Tracks where each value originates: workflow input, tool output, or
literal. Feeds missing-input diagnostics, type checking, and the
explanation of parameter origins.

Status: planned for v0.2.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["analyze_dataflow"]


def analyze_dataflow(ast: object) -> NoReturn:
    """Track value origins across workflow steps. Not implemented yet."""
    raise NotImplementedError("Dataflow analysis is planned for v0.2.0; see docs/PROGRESS.md")
