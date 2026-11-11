"""Tests for the tool registry and tool contract definitions."""

from __future__ import annotations

import pytest

from flowspec.exceptions import DuplicateToolError
from flowspec.registry.tool_registry import ParameterSpec, ToolDefinition, ToolRegistry
from flowspec.typesystem.types import (
    BOOLEAN,
    STRING,
    GenericType,
    NominalType,
)


def _customer_tool() -> ToolDefinition:
    return ToolDefinition(
        name="get_customer",
        description="Find a customer using email.",
        inputs=(ParameterSpec(name="email", type=STRING, required=True),),
        outputs=(
            ParameterSpec(name="customer_id", type=NominalType("CustomerID")),
            ParameterSpec(name="email", type=STRING),
        ),
        effects=("read",),
        permissions=("customers.read",),
    )


def _invoice_tool() -> ToolDefinition:
    return ToolDefinition(
        name="create_invoice",
        inputs=(ParameterSpec(name="customer_id", type=NominalType("CustomerID")),),
        outputs=(
            ParameterSpec(
                name="invoice_ids", type=GenericType("List", (NominalType("InvoiceID"),))
            ),
            ParameterSpec(name="updated", type=BOOLEAN, nullable=True),
        ),
        requires_confirmation=True,
    )


def test_register_and_lookup() -> None:
    registry = ToolRegistry()
    registry.register(_customer_tool())
    registry.register(_invoice_tool())

    assert len(registry) == 2
    assert "get_customer" in registry
    assert "missing_tool" not in registry
    assert registry.get("get_customer") is not None
    assert registry.get("missing_tool") is None
    assert registry.tool_names == ("create_invoice", "get_customer")
    assert [tool.name for tool in registry] == ["create_invoice", "get_customer"]


def test_require_raises_for_missing_tool() -> None:
    registry = ToolRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.require("missing_tool")


def test_duplicate_registration_is_rejected() -> None:
    registry = ToolRegistry()
    registry.register(_customer_tool())
    with pytest.raises(DuplicateToolError, match="already registered"):
        registry.register(_customer_tool())


def test_contract_lookups() -> None:
    tool = _customer_tool()
    assert tool.input("email") is not None and tool.input("email").type == STRING
    assert tool.input("missing") is None
    assert tool.output("customer_id") is not None
    assert tool.output("missing") is None
    assert tool.input_names == ("email",)
    assert tool.output_names == ("customer_id", "email")
    assert tool.effects == ("read",)
    assert tool.permissions == ("customers.read",)
    assert not tool.requires_confirmation


def test_defaults_are_explicit() -> None:
    spec = ParameterSpec(name="x", type=STRING)
    assert spec.required and not spec.nullable
    tool = ToolDefinition(name="t")
    assert tool.inputs == () and tool.outputs == ()
    assert tool.description is None
    assert not tool.requires_confirmation


def test_known_nominal_types_collects_nested_names() -> None:
    registry = ToolRegistry()
    registry.register(_customer_tool())
    registry.register(_invoice_tool())

    assert registry.known_nominal_types() == {"CustomerID", "InvoiceID"}


def test_known_nominal_types_empty_registry() -> None:
    assert ToolRegistry().known_nominal_types() == set()
