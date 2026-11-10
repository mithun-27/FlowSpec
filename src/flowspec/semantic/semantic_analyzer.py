"""Semantic analysis of workflow declarations.

Validates declarations after name resolution: unique step IDs, required
tool inputs supplied, references pointing to declared inputs or valid tool
outputs, and workflow outputs referencing existing, compatible expressions.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["SemanticAnalyzer"]


class SemanticAnalyzer:
    """Placeholder for the semantic analyzer. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("SemanticAnalyzer is planned for v0.1.0; see docs/PROGRESS.md")
