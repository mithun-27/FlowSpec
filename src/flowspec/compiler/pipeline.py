"""Compilation pass orchestration.

Runs the ordered pipeline passes (specification §4.1) — source loading,
syntax parsing, AST construction, name resolution, semantic analysis, type
inference, type checking, dependency analysis, graph analysis, dataflow
analysis, constraint analysis, effect analysis, and IR generation —
aggregating diagnostics across passes. A failed mandatory pass prevents
executable IR generation, while partial diagnostics and a non-executable
analysis report may still be produced.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["CompilationPipeline"]


class CompilationPipeline:
    """Placeholder for the compilation pass pipeline. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("CompilationPipeline is planned for v0.1.0; see docs/PROGRESS.md")
