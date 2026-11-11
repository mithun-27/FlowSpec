"""Expression AST nodes.

The v0.1.0 expression categories (specification §5.4): workflow input
references (``$input.email``), step output references
(``$customer.customer_id``), primitive literals, and explicit ``null``.
More complex expressions arrive in later releases.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowspec.ast.nodes import ASTNode

__all__ = [
    "ExpressionNode",
    "InputReferenceNode",
    "LiteralNode",
    "StepReferenceNode",
    "describe_expression",
]

LiteralValue = str | int | float | bool | None


@dataclass(frozen=True)
class ExpressionNode(ASTNode):
    """Base class for expression nodes."""

    @property
    def kind(self) -> str:
        """A stable name for this expression category."""
        return "expression"


@dataclass(frozen=True)
class LiteralNode(ExpressionNode):
    """A primitive literal: string, integer, float, boolean, or null."""

    value: LiteralValue

    @property
    def kind(self) -> str:
        return "literal"


@dataclass(frozen=True)
class InputReferenceNode(ExpressionNode):
    """A reference to a workflow input, e.g. ``$input.email``."""

    name: str

    @property
    def kind(self) -> str:
        return "input_reference"


@dataclass(frozen=True)
class StepReferenceNode(ExpressionNode):
    """A reference to another step's output, e.g. ``$customer.customer_id``."""

    step: str
    output: str

    @property
    def kind(self) -> str:
        return "step_reference"


def describe_expression(node: ExpressionNode) -> str:
    """Render an expression back to its source form."""
    if isinstance(node, InputReferenceNode):
        return f"$input.{node.name}"
    if isinstance(node, StepReferenceNode):
        return f"${node.step}.{node.output}"
    if isinstance(node, LiteralNode):
        value = node.value
        if isinstance(value, str):
            return f'"{value}"'
        return repr(value)
    return node.kind  # pragma: no cover - future expression kinds
