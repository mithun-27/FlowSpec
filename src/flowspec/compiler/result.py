"""Compilation result objects.

``CompilationResult`` reports the outcome of a compilation: success with
IR and an execution plan, or failure with aggregated structured
diagnostics. It never claims success for workflows that failed any
mandatory pass.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["CompilationResult"]


class CompilationResult:
    """Placeholder for the compilation result object. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("CompilationResult is planned for v0.1.0; see docs/PROGRESS.md")
