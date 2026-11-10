"""Circular dependency detection.

Detects cycles in the workflow dependency graph using DFS or strongly
connected components, reporting E301 diagnostics with the cycle path.
Complexity target: O(V + E).

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["detect_cycles"]


def detect_cycles(graph: object) -> NoReturn:
    """Detect circular dependencies in a workflow graph. Not implemented yet."""
    raise NotImplementedError("Cycle detection is planned for v0.1.0; see docs/PROGRESS.md")
