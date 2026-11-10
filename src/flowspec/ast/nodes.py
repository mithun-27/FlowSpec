"""Base AST node definitions for FlowSpec workflows.

Planned node classes (specification §7): ``WorkflowNode``,
``WorkflowInputNode``, ``ToolCallNode``, ``ToolReferenceNode``,
``LiteralNode``, ``ReferenceNode``, ``ObjectNode``, ``ListNode``,
``ConditionalNode``, and ``OutputNode``.

Nodes will be immutable dataclasses that:

- Preserve source locations for diagnostics.
- Preserve node identifiers and original values where useful.
- Support visitors for compiler passes.
- Separate syntax from semantic annotations.
- Never store execution state.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["ASTNode"]


class ASTNode:
    """Placeholder base class for AST nodes. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("AST nodes are planned for v0.1.0; see docs/PROGRESS.md")
