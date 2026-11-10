"""Parallel execution stage scheduling.

Groups independent steps into execution stages for the execution plan,
respecting declared ordering and never violating dependency or effect
constraints.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["build_execution_stages"]


def build_execution_stages(graph: object) -> NoReturn:
    """Group steps into parallel execution stages. Not implemented yet."""
    raise NotImplementedError(
        "Execution stage scheduling is planned for v0.1.0; see docs/PROGRESS.md"
    )
