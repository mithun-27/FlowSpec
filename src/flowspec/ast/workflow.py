"""Workflow-level AST nodes.

``WorkflowNode`` is the root of a parsed workflow: declared inputs, ordered
steps, and outputs. ``ToolCallNode`` holds a step's tool reference and its
input expressions. ``OutputNode`` binds a workflow output name to an
expression.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from flowspec.ast.expressions import ExpressionNode, StepReferenceNode
from flowspec.ast.nodes import ASTNode

__all__ = ["OutputNode", "ToolCallNode", "WorkflowInputNode", "WorkflowNode"]


@dataclass(frozen=True)
class WorkflowInputNode(ASTNode):
    """A declared workflow input: name, type expression, and required flag."""

    name: str
    type_name: str
    required: bool


@dataclass(frozen=True)
class ToolCallNode(ASTNode):
    """A workflow step: unique id, tool reference, and input expressions."""

    id: str
    tool: str
    inputs: Mapping[str, ExpressionNode] = field(default_factory=dict)


@dataclass(frozen=True)
class OutputNode(ASTNode):
    """A workflow output binding: name plus the expression it refers to."""

    name: str
    expression: ExpressionNode


@dataclass(frozen=True)
class WorkflowNode(ASTNode):
    """The root node of a parsed workflow."""

    name: str
    version: str
    description: str | None
    inputs: Mapping[str, WorkflowInputNode] = field(default_factory=dict)
    steps: tuple[ToolCallNode, ...] = ()
    outputs: Mapping[str, OutputNode] = field(default_factory=dict)

    @property
    def input_names(self) -> tuple[str, ...]:
        return tuple(self.inputs.keys())

    @property
    def step_ids(self) -> tuple[str, ...]:
        return tuple(step.id for step in self.steps)

    def find_step(self, step_id: str) -> ToolCallNode | None:
        """Return the (first) step with the given id, if any."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def step_dependencies(self) -> dict[str, tuple[str, ...]]:
        """Map each step id to the ids of steps it consumes outputs from."""
        found: dict[str, set[str]] = {}
        for step in self.steps:
            consumed: set[str] = set()
            for expression in step.inputs.values():
                if isinstance(expression, StepReferenceNode):
                    consumed.add(expression.step)
            found[step.id] = consumed
        return {step_id: tuple(sorted(consumed)) for step_id, consumed in found.items()}
