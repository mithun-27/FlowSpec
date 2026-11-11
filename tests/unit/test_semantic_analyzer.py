"""Tests for semantic analysis against tool contracts (E101/E402/E201/E202/E204)."""

from __future__ import annotations

from pathlib import Path

from tests.helpers import minimal_registry, workflow_from_text

from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.yaml_parser import parse_yaml_document
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.semantic.name_resolution import resolve_workflow
from flowspec.semantic.semantic_analyzer import SemanticAnalyzer


def _analyze(text: str, config=None):
    workflow = workflow_from_text(text)
    registry = minimal_registry()
    resolution = resolve_workflow(workflow, registry)
    analyzer = SemanticAnalyzer(config)
    return analyzer.analyze(workflow, resolution.symbols, registry)


def _codes(diagnostics) -> list[str]:
    return [d.code for d in diagnostics]


def test_valid_workflow_produces_no_diagnostics() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n"
        "    email: {type: string, required: true}\n"
        "    amount: {type: float, required: true}\n"
        "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        "        amount: $input.amount\n"
        "    - id: send\n      tool: send_invoice\n"
        "      inputs:\n        invoice_id: $invoice.invoice_id\n"
        "    - id: payment\n      tool: update_payment_status\n"
        "      inputs:\n"
        "        payment_id: $invoice.payment_id\n"
        '        status: "pending"\n'
        "  outputs:\n"
        "    invoice_id: $invoice.invoice_id\n"
    )
    workflow = workflow_from_text(text)
    registry = minimal_registry()
    resolution = resolve_workflow(workflow, registry)
    inference, diagnostics = SemanticAnalyzer().analyze(workflow, resolution.symbols, registry)
    assert diagnostics == []
    assert inference.get(workflow.steps[0].inputs["email"]) is not None


def test_missing_required_input_is_e101() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
    )
    _, diagnostics = _analyze(text)
    assert _codes(diagnostics) == ["E101"]
    diagnostic = diagnostics[0]
    assert "email" in diagnostic.message
    assert diagnostic.step == "customer"
    assert diagnostic.received == "not supplied"


def test_unknown_argument_is_e402() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n"
        "        email: $input.email\n"
        '        extra: "nope"\n'
    )
    _, diagnostics = _analyze(text)
    assert _codes(diagnostics) == ["E402"]
    diagnostic = diagnostics[0]
    assert "extra" in diagnostic.message
    assert diagnostic.expected is not None and "email" in diagnostic.expected


def test_optional_argument_may_be_omitted() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        "        amount: 1.0\n"
        "    - id: send\n      tool: send_invoice\n"
        "      inputs:\n        invoice_id: $invoice.invoice_id\n"
    )
    # send_invoice's "cc" input is optional and omitted: no E101.
    _, diagnostics = _analyze(text)
    assert diagnostics == []


def test_primitive_type_mismatch_is_e201() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        '        amount: "not-a-number"\n'
    )
    _, diagnostics = _analyze(text)
    assert _codes(diagnostics) == ["E201"]
    diagnostic = diagnostics[0]
    assert diagnostic.expected == "float"
    assert diagnostic.received == "string"


def test_nominal_type_mismatch_is_e202() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        "        amount: 1.0\n"
        "    - id: send\n      tool: send_invoice\n"
        "      inputs:\n        invoice_id: $customer.customer_id\n"
    )
    _, diagnostics = _analyze(text)
    assert _codes(diagnostics) == ["E202"]
    diagnostic = diagnostics[0]
    assert diagnostic.expected == "InvoiceID"
    assert diagnostic.received == "CustomerID"
    assert diagnostic.step == "send"


def test_null_to_non_nullable_is_e204() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: null\n"
    )
    _, diagnostics = _analyze(text)
    assert _codes(diagnostics) == ["E204"]


def test_integer_widens_to_float() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        "        amount: 12\n"
    )
    _, diagnostics = _analyze(text)
    assert diagnostics == []  # integer literal widens to float


def test_unknown_tool_steps_are_skipped() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: ghost\n      tool: delete_customer\n"
        "      inputs:\n        whatever: $input.nope\n"
    )
    _, diagnostics = _analyze(text)
    # Only the E401 from name resolution context matters here; the analyzer
    # adds nothing for a step without a contract.
    assert diagnostics == []


def test_unresolved_references_are_not_type_checked() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $ghost.customer_id\n"
        "        amount: 1.0\n"
    )
    _, diagnostics = _analyze(text)
    # The unresolved reference is E103 territory (name resolution); the
    # analyzer does not pile a type error on top of it.
    assert diagnostics == []


def test_invoice_example_is_semantically_valid(invoice_example_dir: Path) -> None:
    workflow_path = invoice_example_dir / "workflow.yaml"
    document = parse_yaml_document(
        workflow_path.read_text(encoding="utf-8"), file=str(workflow_path)
    )
    workflow = build_workflow_ast(document)
    registry, _ = load_tool_schema(invoice_example_dir / "tools.yaml")
    resolution = resolve_workflow(workflow, registry)
    assert resolution.diagnostics == ()

    inference, diagnostics = SemanticAnalyzer().analyze(workflow, resolution.symbols, registry)
    assert diagnostics == []
    assert inference.get(workflow.outputs["invoice_id"].expression) is not None
