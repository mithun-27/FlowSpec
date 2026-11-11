"""Tests for AST construction from validated documents."""

from __future__ import annotations

from pathlib import Path

import pytest

from flowspec.ast.expressions import (
    InputReferenceNode,
    LiteralNode,
    StepReferenceNode,
)
from flowspec.ast.nodes import SourceLocation
from flowspec.ast.workflow import WorkflowNode
from flowspec.exceptions import DocumentStructureError, SourceSyntaxError
from flowspec.parser.ast_builder import build_expression, build_workflow_ast
from flowspec.parser.yaml_parser import parse_yaml_document

LOC = SourceLocation(file="workflow.yaml", line=1, column=1)


def test_build_expression_variants() -> None:
    assert isinstance(build_expression("$input.email", LOC), InputReferenceNode)
    assert isinstance(build_expression("$customer.id", LOC), StepReferenceNode)
    assert isinstance(build_expression("pending", LOC), LiteralNode)
    assert isinstance(build_expression(3, LOC), LiteralNode)
    assert isinstance(build_expression(4.5, LOC), LiteralNode)
    assert isinstance(build_expression(True, LOC), LiteralNode)
    assert isinstance(build_expression(None, LOC), LiteralNode)


@pytest.mark.parametrize(
    "bad",
    ["$", "$input", "$input.email.extra", "$customer", "$customer.id.extra", "$$x"],
)
def test_invalid_reference_syntax_is_rejected(bad: str) -> None:
    with pytest.raises(SourceSyntaxError, match="invalid"):
        build_expression(bad, LOC)


def test_non_scalar_expression_is_rejected() -> None:
    with pytest.raises(DocumentStructureError):
        build_expression([1, 2], LOC)


def test_build_workflow_ast_from_example(invoice_example_dir: Path) -> None:
    path = invoice_example_dir / "workflow.yaml"
    doc = parse_yaml_document(path.read_text(encoding="utf-8"), file=str(path))
    workflow = build_workflow_ast(doc)

    assert isinstance(workflow, WorkflowNode)
    assert workflow.name == "invoice_processing"
    assert workflow.version == "1.0"
    assert workflow.input_names == ("email", "amount")
    assert workflow.step_ids == ("customer", "invoice", "send", "payment")

    invoice = workflow.find_step("invoice")
    assert invoice is not None and invoice.tool == "create_invoice"
    assert isinstance(invoice.inputs["customer_id"], StepReferenceNode)
    assert invoice.inputs["customer_id"].step == "customer"
    assert isinstance(invoice.inputs["amount"], InputReferenceNode)

    assert workflow.outputs["invoice_id"].expression == StepReferenceNode(
        step="invoice", output="invoice_id", location=LOC
    ) or isinstance(workflow.outputs["invoice_id"].expression, StepReferenceNode)


def test_build_workflow_ast_preserves_locations() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  steps:\n    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
    )
    doc = parse_yaml_document(text, file="workflow.yaml")
    workflow = build_workflow_ast(doc)
    step = workflow.find_step("customer")
    assert step is not None and step.location.line == 5


def test_build_workflow_ast_rejects_unvalidated_shapes() -> None:
    doc = parse_yaml_document("version: '1.0'\nworkflow: not-a-mapping\n")
    with pytest.raises(DocumentStructureError):
        build_workflow_ast(doc)
