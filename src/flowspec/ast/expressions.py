"""Expression AST nodes.

Planned nodes for the initial expression categories (specification §5.4):
workflow input references (``$input.email``), step output references
(``$customer.customer_id``), primitive literals, and explicit ``null``
literals. More complex expressions arrive in later releases.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["ExpressionNode"]


class ExpressionNode:
    """Placeholder base class for expression AST nodes. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("Expression nodes are planned for v0.1.0; see docs/PROGRESS.md")
