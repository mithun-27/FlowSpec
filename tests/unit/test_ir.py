"""Tests for the intermediate representation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.helpers import workflow_from_text

from flowspec import __version__
from flowspec.compiler.ir import IR_VERSION, IntermediateRepresentation
from flowspec.exceptions import InternalError
from flowspec.graph.graph import WorkflowGraph
from flowspec.graph.scheduler import build_execution_stages
from flowspec.graph.topological_sort import topological_sort
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.semantic.name_resolution import resolve_workflow
from flowspec.typesystem.inference import infer_expression_types


def _example_state(invoice_example_dir: Path):
    """The fully compiled state of the valid invoice example."""
    workflow = workflow_from_text(
        (invoice_example_dir / "workflow.yaml").read_text(encoding="utf-8")
    )
    registry, diagnostics = load_tool_schema(invoice_example_dir / "tools.yaml")
    assert diagnostics == []
    symbols = resolve_workflow(workflow, registry).symbols
    inference, _ = infer_expression_types(workflow, symbols)
    graph = WorkflowGraph.from_workflow(workflow, symbols)
    order = topological_sort(graph)
    stages = build_execution_stages(graph)
    assert order is not None and stages is not None
    return workflow, registry, inference, graph, tuple(order), stages


def _build_ir(invoice_example_dir: Path) -> IntermediateRepresentation:
    workflow, registry, inference, graph, order, stages = _example_state(invoice_example_dir)
    return IntermediateRepresentation.build(workflow, registry, inference, graph, order, stages)


def test_ir_carries_the_full_compiled_contract(invoice_example_dir: Path) -> None:
    ir = _build_ir(invoice_example_dir)

    assert ir.workflow_name == "invoice_processing"
    assert ir.description == "Complete invoice processing workflow."
    assert ir.schema_version == "1.0"
    assert ir.ir_version == IR_VERSION == "1.0"
    assert ir.compiler_version == __version__

    # Workflow inputs keep declaration order and explicit types.
    assert [(item.name, item.type, item.required) for item in ir.inputs] == [
        ("email", "string", True),
        ("amount", "float", True),
    ]

    # Workflow outputs bind sources to their inferred types.
    assert [(item.name, item.source, item.type) for item in ir.outputs] == [
        ("invoice_id", "$invoice.invoice_id", "InvoiceID"),
        ("payment_updated", "$payment.updated", "boolean"),
    ]

    # Steps keep declaration order with positions and dependencies.
    assert [(step.id, step.tool, step.position) for step in ir.steps] == [
        ("customer", "get_customer", 0),
        ("invoice", "create_invoice", 1),
        ("send", "send_invoice", 2),
        ("payment", "update_payment_status", 3),
    ]
    by_id = {step.id: step for step in ir.steps}
    assert by_id["customer"].dependencies == ()
    assert by_id["invoice"].dependencies == ("customer",)
    assert by_id["send"].dependencies == ("invoice",)
    assert by_id["payment"].dependencies == ("invoice",)


def test_ir_step_contracts(invoice_example_dir: Path) -> None:
    ir = _build_ir(invoice_example_dir)
    by_id = {step.id: step for step in ir.steps}

    # Supplied arguments: source expression plus inferred type.
    payment = by_id["payment"]
    assert [(item.argument, item.source, item.type) for item in payment.inputs] == [
        ("payment_id", "$invoice.payment_id", "PaymentID"),
        ("status", '"pending"', "string"),
    ]
    # Declared outputs with nullability.
    assert [(item.name, item.type, item.nullable) for item in payment.outputs] == [
        ("updated", "boolean", False)
    ]
    # Effects, permissions, and confirmation flags survive compilation.
    assert payment.effects == ("write",)
    assert payment.permissions == ("payments.update",)
    assert not payment.requires_confirmation
    assert by_id["send"].effects == ("external_write",)

    invoice = by_id["invoice"]
    assert [(item.argument, item.source) for item in invoice.inputs] == [
        ("amount", "$input.amount"),
        ("customer_id", "$customer.customer_id"),
    ]


def test_ir_execution_plan_and_metadata(invoice_example_dir: Path) -> None:
    ir = _build_ir(invoice_example_dir)

    assert ir.order == ("customer", "invoice", "payment", "send")
    assert ir.stages == (("customer",), ("invoice",), ("payment", "send"))
    assert ir.effects == ("external_write", "read", "write")
    assert ir.permissions == (
        "customers.read",
        "invoices.create",
        "invoices.send",
        "payments.update",
    )
    graph = ir.graph
    assert isinstance(graph, dict)
    assert graph["steps"] == ["customer", "invoice", "send", "payment"]
    assert graph["adjacency"]["invoice"] == ["payment", "send"]


def test_ir_serialization_is_deterministic(invoice_example_dir: Path) -> None:
    first = _build_ir(invoice_example_dir)
    second = _build_ir(invoice_example_dir)

    assert first == second
    assert first.to_json() == second.to_json()
    assert first.to_dict() == second.to_dict()


def test_ir_json_roundtrip(invoice_example_dir: Path) -> None:
    ir = _build_ir(invoice_example_dir)

    parsed = json.loads(ir.to_json())

    assert parsed == ir.to_dict()
    assert parsed["ir_version"] == "1.0"
    assert parsed["execution"]["order"] == ["customer", "invoice", "payment", "send"]
    assert parsed["execution"]["stages"] == [["customer"], ["invoice"], ["payment", "send"]]
    assert parsed["metadata"]["effects"] == ["external_write", "read", "write"]


def test_ir_to_dict_has_stable_top_level_keys(invoice_example_dir: Path) -> None:
    ir = _build_ir(invoice_example_dir)

    assert set(ir.to_dict()) == {
        "ir_version",
        "compiler_version",
        "workflow",
        "steps",
        "execution",
        "graph",
        "metadata",
    }


def test_build_refuses_untyped_expressions(invoice_example_dir: Path) -> None:
    """An expression that was never inferred must not produce broken IR."""
    workflow = workflow_from_text(
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.nope\n"
    )
    registry, _ = load_tool_schema(invoice_example_dir / "tools.yaml")
    symbols = resolve_workflow(workflow, registry).symbols
    inference, _ = infer_expression_types(workflow, symbols)
    graph = WorkflowGraph.from_workflow(workflow, symbols)
    order = topological_sort(graph)
    assert order is not None

    with pytest.raises(InternalError):
        IntermediateRepresentation.build(workflow, registry, inference, graph, tuple(order), None)
