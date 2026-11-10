"""Execution planning.

Turns validated IR into a concrete execution plan that respects dependency
ordering, identifies independent operations, preserves effect metadata,
and respects approval requirements. Automatic retries and compensation
logic are out of scope for the initial compiler.

Status: planned; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["ExecutionPlanner"]


class ExecutionPlanner:
    """Placeholder for the execution planner. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("ExecutionPlanner is planned; see docs/PROGRESS.md")
