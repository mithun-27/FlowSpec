"""The workflow dependency graph.

A directed graph over workflow steps using adjacency lists and reverse
adjacency lists. Edges retain source step, destination step, source output,
destination input, type information, and source location — everything later
passes need for diagnostics and scheduling.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["WorkflowGraph"]


class WorkflowGraph:
    """Placeholder for the workflow dependency graph. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("WorkflowGraph is planned for v0.1.0; see docs/PROGRESS.md")
