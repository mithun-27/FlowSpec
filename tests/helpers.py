"""Shared helpers for building parsed workflows and registries in tests."""

from __future__ import annotations

from flowspec.ast.workflow import WorkflowNode
from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.yaml_parser import parse_yaml_document
from flowspec.registry.schema_loader import load_tool_document
from flowspec.registry.tool_registry import ToolRegistry


def workflow_from_text(text: str, file: str = "workflow.yaml") -> WorkflowNode:
    """Parse workflow YAML text into an AST."""
    document = parse_yaml_document(text, file=file)
    return build_workflow_ast(document)


def registry_from_text(text: str) -> ToolRegistry:
    """Parse tool registry YAML text; asserts the contract is valid."""
    document = parse_yaml_document(text, file="tools.yaml")
    registry, diagnostics = load_tool_document(document)
    assert diagnostics == []
    return registry


# A minimal registry used by semantic tests: mirrors the shapes of the
# invoice example without the ceremony.
TOOLS_YAML = """
version: '1.0'

tools:

  get_customer:
    inputs:
      email: {type: string, required: true}
    outputs:
      customer_id: {type: CustomerID}
      email: {type: string}

  create_invoice:
    inputs:
      customer_id: {type: CustomerID}
      amount: {type: float}
    outputs:
      invoice_id: {type: InvoiceID}
      payment_id: {type: PaymentID}

  send_invoice:
    inputs:
      invoice_id: {type: InvoiceID, required: true}
      cc: {type: string, required: false}
    outputs:
      status: {type: string}

  update_payment_status:
    inputs:
      payment_id: {type: PaymentID}
      status: {type: string}
    outputs:
      updated: {type: boolean}
"""


def minimal_registry() -> ToolRegistry:
    return registry_from_text(TOOLS_YAML)


def workflow_header(inputs: str = "", outputs: str = "") -> str:
    """The standard workflow YAML preamble used by semantic tests."""
    parts = ["version: '1.0'", "", "workflow:", "  name: test_workflow", ""]
    if inputs:
        parts.append("  inputs:")
        parts.append(inputs)
        parts.append("")
    parts.append("  steps:")
    if outputs:
        parts.append("")
        parts.append("  outputs:")
        parts.append(outputs)
    return "\n".join(parts) + "\n"
