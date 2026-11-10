"""Reachability and dead-step analysis.

Finds steps that cannot contribute to workflow outputs or required side
effects (E303). Dead steps are reported as diagnostics — never removed
automatically.

Status: planned for v0.2.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["analyze_reachability"]


def analyze_reachability(graph: object) -> NoReturn:
    """Analyze reachability of workflow steps. Not implemented yet."""
    raise NotImplementedError("Reachability analysis is planned for v0.2.0; see docs/PROGRESS.md")
