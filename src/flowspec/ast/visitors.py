"""Visitor protocol for traversing the FlowSpec AST.

Compiler passes will use visitors to walk the AST without embedding
traversal logic inside node definitions.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["ASTVisitor"]


class ASTVisitor:
    """Placeholder base class for AST visitors. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("AST visitors are planned for v0.1.0; see docs/PROGRESS.md")
