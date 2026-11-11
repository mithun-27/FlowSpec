"""Tests for expression type inference and the unknown-nominal policy."""

from __future__ import annotations

from pathlib import Path

import pytest

from flowspec.ast.expressions import (
    InputReferenceNode,
    LiteralNode,
    StepReferenceNode,
)
from flowspec.ast.nodes import SourceLocation
from flowspec.ast.workflow import OutputNode, ToolCallNode, WorkflowNode
from flowspec.config import CompilerConfig
from flowspec.exceptions import InternalError
from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.yaml_parser import parse_yaml_document
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.registry.tool_registry import ParameterSpec
from flowspec.typesystem.inference import infer_expression_types
from flowspec.typesystem.parser import parse_type
from flowspec.typesystem.symbols import InputSymbol, StepSymbol, SymbolTable
from flowspec.typesystem.types import (
    BOOLEAN,
    FLOAT,
    INTEGER,
    NULL,
    STRING,
    GenericType,
    NominalType,
)

LOC = SourceLocation(file="workflow.yaml", line=1, column=1)


def _symbols(workflow: WorkflowNode, registry) -> SymbolTable:
    """Build the symbol table name resolution will produce (Stage C)."""
    symbols = SymbolTable(known_nominal_types=registry.known_nominal_types())
    for name, spec in workflow.inputs.items():
        symbols.declare_input(InputSymbol(name, parse_type(spec.type_name), spec.required))
    for step in workflow.steps:
        tool = registry.get(step.tool)
        outputs = SymbolTable.from_registry_tool(tool) if tool else {}
        symbols.declare_step(StepSymbol(step.id, step.tool, outputs))
    return symbols


def test_literal_type_inference() -> None:
    workflow = WorkflowNode(
        name="literals",
        version="1.0",
        description=None,
        location=LOC,
        steps=(
            ToolCallNode(
                id="s",
                tool="t",
                inputs={
                    "a_str": LiteralNode(value="x", location=LOC),
                    "an_int": LiteralNode(value=3, location=LOC),
                    "a_float": LiteralNode(value=3.5, location=LOC),
                    "a_bool": LiteralNode(value=True, location=LOC),
                    "a_null": LiteralNode(value=None, location=LOC),
                },
                location=LOC,
            ),
        ),
        outputs={},
    )
    inference, diagnostics = infer_expression_types(workflow, SymbolTable())

    assert diagnostics == []
    assert inference.of(workflow.steps[0].inputs["a_str"]) == STRING
    assert inference.of(workflow.steps[0].inputs["an_int"]) == INTEGER
    assert inference.of(workflow.steps[0].inputs["a_float"]) == FLOAT
    # bool must be inferred as boolean, not integer (True is an int in Python).
    assert inference.of(workflow.steps[0].inputs["a_bool"]) == BOOLEAN
    assert inference.of(workflow.steps[0].inputs["a_null"]) == NULL


def test_reference_type_inference() -> None:
    symbols = SymbolTable(known_nominal_types={"CustomerID", "InvoiceID"})
    symbols.declare_input(InputSymbol("email", STRING, True))
    symbols.declare_input(InputSymbol("amount", FLOAT, True))
    symbols.declare_step(
        StepSymbol(
            "invoice",
            "create_invoice",
            outputs={
                "invoice_id": ParameterSpec(name="invoice_id", type=NominalType("InvoiceID")),
                "status": ParameterSpec(name="status", type=STRING, nullable=True),
            },
        )
    )

    email_ref = InputReferenceNode(name="email", location=LOC)
    amount_ref = InputReferenceNode(name="amount", location=LOC)
    invoice_ref = StepReferenceNode(step="invoice", output="invoice_id", location=LOC)
    status_ref = StepReferenceNode(step="invoice", output="status", location=LOC)

    workflow = WorkflowNode(
        name="refs",
        version="1.0",
        description=None,
        location=LOC,
        inputs={},
        steps=(
            ToolCallNode(
                id="s",
                tool="t",
                inputs={
                    "email": email_ref,
                    "amount": amount_ref,
                    "invoice_id": invoice_ref,
                    "status": status_ref,
                },
                location=LOC,
            ),
        ),
        outputs={"invoice_id": OutputNode(name="invoice_id", expression=invoice_ref, location=LOC)},
    )
    inference, diagnostics = infer_expression_types(workflow, symbols)

    assert diagnostics == []
    assert inference.of(email_ref) == STRING
    assert inference.of(amount_ref) == FLOAT
    assert inference.of(invoice_ref) == NominalType("InvoiceID")
    # Nullable outputs get the Optional[T] effective type.
    assert inference.of(status_ref) == GenericType("Optional", (STRING,))
    # The output binding expression shares the node's inferred type.
    assert inference.of(workflow.outputs["invoice_id"].expression) is not None


def test_unresolved_references_are_skipped() -> None:
    missing_input = InputReferenceNode(name="nope", location=LOC)
    missing_output = StepReferenceNode(step="ghost", output="x", location=LOC)
    workflow = WorkflowNode(
        name="unresolved",
        version="1.0",
        description=None,
        location=LOC,
        steps=(
            ToolCallNode(
                id="s",
                tool="t",
                inputs={"a": missing_input, "b": missing_output},
                location=LOC,
            ),
        ),
        outputs={},
    )
    inference, diagnostics = infer_expression_types(workflow, SymbolTable())

    # Resolution failures are reported by name resolution (Stage C), not here.
    assert diagnostics == []
    assert inference.get(missing_input) is None
    assert inference.get(missing_output) is None
    with pytest.raises(InternalError):
        inference.of(missing_input)


def test_unknown_nominal_input_type_is_e203_in_strict_mode() -> None:
    symbols = SymbolTable(known_nominal_types={"CustomerID"})
    symbols.declare_input(InputSymbol("widget", NominalType("WidgetID"), True))
    workflow = WorkflowNode(
        name="unknown-type",
        version="1.0",
        description=None,
        location=LOC,
        steps=(),
        outputs={},
    )
    _, diagnostics = infer_expression_types(workflow, symbols)
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "E203"
    assert "WidgetID" in diagnostics[0].message


def test_unknown_nominal_input_type_allowed_when_configured() -> None:
    symbols = SymbolTable(known_nominal_types={"CustomerID"})
    symbols.declare_input(InputSymbol("widget", NominalType("WidgetID"), True))
    workflow = WorkflowNode(
        name="unknown-type",
        version="1.0",
        description=None,
        location=LOC,
        steps=(),
        outputs={},
    )
    config = CompilerConfig(allow_unknown_types=True)
    _, diagnostics = infer_expression_types(workflow, symbols, config)
    assert diagnostics == []


def test_known_nominal_input_type_passes() -> None:
    symbols = SymbolTable(known_nominal_types={"CustomerID", "InvoiceID"})
    symbols.declare_input(InputSymbol("cid", NominalType("CustomerID"), True))
    workflow = WorkflowNode(
        name="known-type",
        version="1.0",
        description=None,
        location=LOC,
        steps=(),
        outputs={},
    )
    _, diagnostics = infer_expression_types(workflow, symbols)
    assert diagnostics == []


def test_invoice_example_infers_every_expression(invoice_example_dir: Path) -> None:
    """End-to-end: example workflow + example registry → fully typed, no diagnostics."""
    workflow_path = invoice_example_dir / "workflow.yaml"
    document = parse_yaml_document(
        workflow_path.read_text(encoding="utf-8"), file=str(workflow_path)
    )
    workflow = build_workflow_ast(document)
    registry, registry_diagnostics = load_tool_schema(invoice_example_dir / "tools.yaml")
    assert registry_diagnostics == []

    symbols = _symbols(workflow, registry)
    inference, diagnostics = infer_expression_types(workflow, symbols)

    assert diagnostics == []
    # Every expression in the valid workflow is typed.
    for step in workflow.steps:
        for expression in step.inputs.values():
            assert inference.get(expression) is not None, f"{step.id}.{expression}"
    for output in workflow.outputs.values():
        assert inference.get(output.expression) is not None

    customer_step = workflow.find_step("customer")
    assert customer_step is not None
    assert inference.of(customer_step.inputs["email"]) == STRING

    invoice_step = workflow.find_step("invoice")
    assert invoice_step is not None
    assert inference.of(invoice_step.inputs["customer_id"]) == NominalType("CustomerID")
    assert inference.of(invoice_step.inputs["amount"]) == FLOAT

    payment_step = workflow.find_step("payment")
    assert payment_step is not None
    assert inference.of(payment_step.inputs["status"]) == STRING
