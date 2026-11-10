"""Static analysis orchestration.

Runs the individual analyzers — missing input, reference validity, type
compatibility, optional values, cycles, permissions, effects, and outputs —
against a resolved workflow and aggregates their structured diagnostics.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["StaticAnalyzer"]


class StaticAnalyzer:
    """Placeholder for the static analysis orchestrator. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("StaticAnalyzer is planned for v0.1.0; see docs/PROGRESS.md")
