"""Tests for AST nodes, expression descriptions, and traversal."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from flowspec.ast.expressions import (
    InputReferenceNode,
    LiteralNode,
    StepReferenceNode,
    describe_expression,
)
from flowspec.ast.nodes import SourceLocation
from flowspec.ast.visitors import ASTVisitor, walk
from flowspec.ast.workflow import OutputNode, ToolCallNode, WorkflowInputNode, WorkflowNode

LOC = SourceLocation(file="workflow.yaml", line=1, column=1)


def _workflow() -> WorkflowNode:
    return WorkflowNode(
        name="w",
        version="1.0",
        description=None,
        location=LOC,
        inputs={
            "email": WorkflowInputNode(
                name="email", type_name="string", required=True, location=LOC
            )
        },
        steps=(
            ToolCallNode(
                id="customer",
                tool="get_customer",
                inputs={"email": InputReferenceNode(name="email", location=LOC)},
                location=LOC,
            ),
            ToolCallNode(
                id="invoice",
                tool="create_invoice",
                inputs={
                    "customer_id": StepReferenceNode(
                        step="customer", output="customer_id", location=LOC
                    ),
                    "amount": LiteralNode(value=99.5, location=LOC),
                },
                location=LOC,
            ),
        ),
        outputs={
            "invoice_id": OutputNode(
                name="invoice_id",
                expression=StepReferenceNode(step="invoice", output="invoice_id", location=LOC),
                location=LOC,
            )
        },
    )


def test_source_location_rendering() -> None:
    assert str(SourceLocation("a.yaml", 3, 7)) == "a.yaml:3:7"
    assert str(SourceLocation.unknown("a.yaml")) == "a.yaml"


def test_nodes_are_frozen() -> None:
    literal = LiteralNode(value="x", location=LOC)
    with pytest.raises(FrozenInstanceError):
        literal.value = "y"  # type: ignore[misc]


def test_equal_expressions_at_different_locations_are_distinct() -> None:
    first = LiteralNode(value="pending", location=LOC)
    second = LiteralNode(value="pending", location=SourceLocation("w.yaml", 9, 1))
    assert first == LiteralNode(value="pending", location=LOC)
    assert first != second


def test_describe_expression_roundtrip() -> None:
    assert describe_expression(InputReferenceNode(name="email", location=LOC)) == "$input.email"
    assert (
        describe_expression(StepReferenceNode(step="customer", output="id", location=LOC))
        == "$customer.id"
    )
    assert describe_expression(LiteralNode(value="pending", location=LOC)) == '"pending"'
    assert describe_expression(LiteralNode(value=None, location=LOC)) == "None"
    assert describe_expression(LiteralNode(value=True, location=LOC)) == "True"


def test_walk_visits_every_node() -> None:
    kinds = [type(node).__name__ for node in walk(_workflow())]
    assert kinds.count("ToolCallNode") == 2
    assert kinds.count("InputReferenceNode") == 1
    assert kinds.count("StepReferenceNode") == 2
    assert kinds.count("LiteralNode") == 1
    assert kinds.count("WorkflowNode") == 1
    assert kinds.count("OutputNode") == 1


def test_visitor_dispatch() -> None:
    visited: list[str] = []

    class Collector(ASTVisitor):
        def visit_LiteralNode(self, node: LiteralNode) -> None:
            visited.append(repr(node.value))

    Collector().visit(LiteralNode(value=5, location=LOC))
    assert visited == ["5"]

    class NoHooks(ASTVisitor):
        pass

    NoHooks().visit(_workflow())  # every node falls through to generic_visit


def test_workflow_helpers() -> None:
    workflow = _workflow()
    assert workflow.step_ids == ("customer", "invoice")
    assert workflow.input_names == ("email",)
    assert workflow.find_step("invoice") is not None
    assert workflow.find_step("missing") is None
    assert workflow.step_dependencies() == {"customer": (), "invoice": ("customer",)}
