"""Visitor protocol for traversing the FlowSpec AST.

Compiler passes walk the AST through :func:`walk` or subclass
:class:`ASTVisitor` instead of embedding traversal logic in node
definitions.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Iterator

from flowspec.ast.expressions import (
    ExpressionNode,
    InputReferenceNode,
    LiteralNode,
    StepReferenceNode,
)
from flowspec.ast.nodes import ASTNode
from flowspec.ast.workflow import OutputNode, ToolCallNode, WorkflowInputNode, WorkflowNode

__all__ = ["ASTVisitor", "walk"]


def _children(node: ASTNode) -> list[ASTNode]:
    """The direct children of ``node`` in source order."""
    children: list[ASTNode] = []
    if isinstance(node, WorkflowNode):
        children.extend(node.inputs.values())
        children.extend(node.steps)
        children.extend(node.outputs.values())
    elif isinstance(node, ToolCallNode):
        children.extend(node.inputs.values())
    elif isinstance(node, OutputNode):
        children.append(node.expression)
    return children


def walk(node: ASTNode) -> Iterator[ASTNode]:
    """Yield ``node`` and all of its descendants in source order."""
    yield node
    for child in _children(node):
        yield from walk(child)


class ASTVisitor:
    """Base class for AST visitors.

    Subclasses override the ``visit_*`` methods they care about; unknown
    node kinds fall through to :meth:`generic_visit`.
    """

    def visit(self, node: ASTNode) -> None:
        """Dispatch to the ``visit_*`` method matching the node type."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is not None and callable(method):
            method(node)  # type: ignore[call-arg]
        else:
            self.generic_visit(node)

    def generic_visit(self, node: ASTNode) -> None:
        """Called for node kinds without a specific visitor method."""

    # Node-specific hooks (override as needed).
    def visit_WorkflowNode(self, node: WorkflowNode) -> None:
        self.generic_visit(node)

    def visit_WorkflowInputNode(self, node: WorkflowInputNode) -> None:
        self.generic_visit(node)

    def visit_ToolCallNode(self, node: ToolCallNode) -> None:
        self.generic_visit(node)

    def visit_OutputNode(self, node: OutputNode) -> None:
        self.generic_visit(node)

    def visit_LiteralNode(self, node: LiteralNode) -> None:
        self.generic_visit(node)

    def visit_InputReferenceNode(self, node: InputReferenceNode) -> None:
        self.generic_visit(node)

    def visit_StepReferenceNode(self, node: StepReferenceNode) -> None:
        self.generic_visit(node)

    def visit_ExpressionNode(self, node: ExpressionNode) -> None:
        self.generic_visit(node)
