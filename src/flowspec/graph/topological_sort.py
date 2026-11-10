"""Topological sorting of the workflow graph.

Produces a valid execution order using Kahn's algorithm (O(V + E)); a cyclic
graph yields E302 invalid-execution-order diagnostics instead of an order.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["topological_sort"]


def topological_sort(graph: object) -> NoReturn:
    """Compute a topological execution order. Not implemented yet."""
    raise NotImplementedError("Topological sorting is planned for v0.1.0; see docs/PROGRESS.md")
