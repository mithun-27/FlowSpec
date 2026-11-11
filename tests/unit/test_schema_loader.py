"""Tests for tool schema loading into the registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from flowspec.config import CompilerConfig
from flowspec.exceptions import ConfigurationError, SourceSyntaxError
from flowspec.parser.yaml_parser import parse_yaml_document
from flowspec.registry.schema_loader import load_tool_document, load_tool_schema
from flowspec.typesystem.types import (
    STRING,
    GenericType,
    NominalType,
    PrimitiveType,
)


def test_loads_the_invoice_example(invoice_example_dir: Path) -> None:
    registry, diagnostics = load_tool_schema(invoice_example_dir / "tools.yaml")

    assert diagnostics == []
    assert registry.tool_names == (
        "create_invoice",
        "get_customer",
        "send_invoice",
        "update_payment_status",
    )
    assert registry.known_nominal_types() == {
        "CustomerID",
        "InvoiceID",
        "PaymentID",
    }


def test_invoice_example_contracts_parse_to_internal_types(
    invoice_example_dir: Path,
) -> None:
    registry, _ = load_tool_schema(invoice_example_dir / "tools.yaml")

    get_customer = registry.require("get_customer")
    assert get_customer.input("email") is not None
    assert get_customer.input("email").type == STRING
    assert get_customer.output("customer_id").type == NominalType("CustomerID")
    assert not get_customer.output("customer_id").nullable
    assert get_customer.effects == ("read",)
    assert get_customer.permissions == ("customers.read",)

    create_invoice = registry.require("create_invoice")
    assert create_invoice.input("customer_id").type == NominalType("CustomerID")
    assert create_invoice.input("customer_id").required
    assert create_invoice.input("amount").type == PrimitiveType("float")

    send_invoice = registry.require("send_invoice")
    assert send_invoice.output("status").type == STRING
    assert send_invoice.effects == ("external_write",)


def test_load_tool_document_with_bad_type_expression() -> None:
    text = "version: '1.0'\ntools:\n  broken:\n    inputs:\n      x:\n        type: 'List['\n"
    document = parse_yaml_document(text, file="tools.yaml")
    registry, diagnostics = load_tool_document(document)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == "E205"
    assert diagnostic.is_error
    assert "broken" in diagnostic.message and "x" in diagnostic.message

    # The tool is still registered; only the broken parameter is dropped.
    broken = registry.require("broken")
    assert broken.input("x") is None


def test_structural_errors_short_circuit() -> None:
    document = parse_yaml_document("version: '1.0'\ntools: not-a-mapping\n")
    registry, diagnostics = load_tool_document(document)

    assert diagnostics and all(d.code == "E002" for d in diagnostics)
    assert len(registry) == 0


def test_missing_file_is_a_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_tool_schema(tmp_path / "missing.yaml")


def test_config_passes_parser_limits(tmp_path: Path) -> None:
    path = tmp_path / "tools.yaml"
    path.write_text("version: '1.0'\ntools: {}\n", encoding="utf-8")
    strict_config = CompilerConfig(max_document_size=2)
    with pytest.raises(SourceSyntaxError, match="maximum size"):
        load_tool_schema(path, strict_config)


def test_optional_parameter_flag_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "tools.yaml"
    path.write_text(
        "version: '1.0'\n"
        "tools:\n"
        "  t:\n"
        "    inputs:\n"
        "      a:\n"
        "        type: Optional[CustomerID]\n"
        "        required: false\n"
        "        nullable: true\n"
        "    outputs:\n"
        "      b:\n"
        "        type: List[string]\n",
        encoding="utf-8",
    )
    registry, diagnostics = load_tool_schema(path)
    assert diagnostics == []

    tool = registry.require("t")
    assert tool.input("a").type == GenericType("Optional", (NominalType("CustomerID"),))
    assert not tool.input("a").required
    assert tool.input("a").nullable
    assert tool.output("b").type == GenericType("List", (STRING,))
