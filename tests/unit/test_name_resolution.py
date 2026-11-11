"""Tests for workflow name resolution (E401/E304/E102/E103/E205)."""

from __future__ import annotations

from pathlib import Path

from tests.helpers import minimal_registry, workflow_from_text

from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.yaml_parser import parse_yaml_document
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.semantic.name_resolution import resolve_workflow


def _resolve(text: str, registry=None):
    workflow = workflow_from_text(text)
    return resolve_workflow(workflow, registry or minimal_registry())


def _codes(diagnostics) -> list[str]:
    return [d.code for d in diagnostics]


def test_valid_example_resolves_cleanly(invoice_example_dir: Path) -> None:
    workflow_path = invoice_example_dir / "workflow.yaml"
    document = parse_yaml_document(
        workflow_path.read_text(encoding="utf-8"), file=str(workflow_path)
    )
    workflow = build_workflow_ast(document)
    registry, registry_diagnostics = load_tool_schema(invoice_example_dir / "tools.yaml")
    assert registry_diagnostics == []

    resolution = resolve_workflow(workflow, registry)

    assert resolution.diagnostics == ()
    symbols = resolution.symbols
    assert set(symbols.inputs) == {"email", "amount"}
    assert set(symbols.steps) == {"customer", "invoice", "send", "payment"}
    assert set(symbols.outputs) == set()
    assert symbols.known_nominal_types == {"CustomerID", "InvoiceID", "PaymentID"}
    customer = symbols.resolve_step("customer")
    assert customer is not None and customer.contract_known
    assert set(customer.outputs) == {"customer_id", "email"}


def test_unknown_tool_is_e401() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: ghost\n      tool: delete_customer\n"
    )
    resolution = _resolve(text)
    assert _codes(resolution.diagnostics) == ["E401"]
    diagnostic = resolution.diagnostics[0]
    assert "delete_customer" in diagnostic.message
    assert diagnostic.step == "ghost"
    ghost = resolution.symbols.resolve_step("ghost")
    assert ghost is not None and not ghost.contract_known


_EMAIL_INPUTS = "  inputs:\n    email: {type: string, required: true}\n"


def test_duplicate_step_id_is_e304() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: a\n      tool: send_invoice\n"
    )
    resolution = _resolve(text)
    assert _codes(resolution.diagnostics) == ["E304"]
    assert resolution.diagnostics[0].step == "a"


def test_unknown_workflow_input_reference_is_e103() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.no_such_input\n"
    )
    resolution = _resolve(text)
    assert _codes(resolution.diagnostics) == ["E103"]
    assert "$input.no_such_input" in resolution.diagnostics[0].received


def test_unknown_step_reference_is_e103() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $ghost.customer_id\n"
        "        amount: 1.5\n"
    )
    resolution = _resolve(text)
    assert _codes(resolution.diagnostics) == ["E103"]
    assert "unknown step" in resolution.diagnostics[0].message


def test_unknown_output_reference_is_e102() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        "        amount: 2.0\n"
        "    - id: send\n      tool: send_invoice\n"
        "      inputs:\n        invoice_id: $invoice.updated\n"
    )
    resolution = _resolve(text)
    assert _codes(resolution.diagnostics) == ["E102"]
    diagnostic = resolution.diagnostics[0]
    assert "updated" in diagnostic.message
    assert "invoice_id" in diagnostic.expected or "payment_id" in diagnostic.expected


def test_malformed_input_type_is_e205_without_reference_cascade() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n    broken: {type: 'List['}\n"
        "  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.broken\n"
    )
    resolution = _resolve(text)
    assert _codes(resolution.diagnostics) == ["E205"]
    assert "broken" in resolution.diagnostics[0].message


def test_unknown_tool_step_does_not_cascade_on_references_to_it() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: ghost\n      tool: delete_customer\n"
        "    - id: a\n      tool: send_invoice\n"
        "      inputs:\n        invoice_id: $ghost.whatever\n"
    )
    resolution = _resolve(text)
    # Only the unknown tool itself is reported — not a follow-on E102/E103.
    assert _codes(resolution.diagnostics) == ["E401"]


def test_forward_references_are_allowed() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        "        amount: 1.0\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
    )
    resolution = _resolve(text)
    assert resolution.diagnostics == ()


def test_workflow_outputs_are_checked_too() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "  outputs:\n"
        "    thing: $customer.nope\n"
    )
    resolution = _resolve(text)
    assert _codes(resolution.diagnostics) == ["E102"]
    assert "workflow output" in resolution.diagnostics[0].message
