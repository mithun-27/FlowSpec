"""Tests for type definitions and type expression parsing."""

from __future__ import annotations

import pytest

from flowspec.exceptions import TypeParseError
from flowspec.typesystem.parser import parse_type
from flowspec.typesystem.types import (
    ANY,
    BOOLEAN,
    FLOAT,
    INTEGER,
    NULL,
    STRING,
    GenericType,
    NominalType,
    ObjectType,
    PrimitiveType,
    PropertySpec,
    is_any,
    is_null,
    is_optional,
    optional_of,
)


def test_primitive_singletons() -> None:
    assert PrimitiveType("string") == STRING
    assert INTEGER.render() == "integer"
    assert FLOAT.render() == "float"
    assert BOOLEAN.render() == "boolean"
    assert NULL.render() == "null"
    assert ANY.render() == "any"
    assert is_any(ANY) and is_null(NULL)
    assert not is_optional(STRING)


def test_parse_primitives_and_nominals() -> None:
    assert parse_type("string") == STRING
    assert parse_type("float") == FLOAT
    assert parse_type("CustomerID") == NominalType("CustomerID")
    assert parse_type("CustomerID").render() == "CustomerID"
    assert parse_type("  string  ") == STRING


def test_parse_generics() -> None:
    listed = parse_type("List[InvoiceID]")
    assert listed == GenericType("List", (NominalType("InvoiceID"),))
    assert listed.render() == "List[InvoiceID]"

    assert parse_type("Optional[CustomerID]") == GenericType(
        "Optional", (NominalType("CustomerID"),)
    )
    assert parse_type("Dict[string, integer]") == GenericType("Dict", (STRING, INTEGER))
    assert parse_type("Union[CustomerID, InvoiceID]") == GenericType(
        "Union", (NominalType("CustomerID"), NominalType("InvoiceID"))
    )
    assert parse_type("List[Optional[CustomerID]]").render() == "List[Optional[CustomerID]]"
    assert is_optional(parse_type("Optional[CustomerID]"))
    assert optional_of(parse_type("Optional[CustomerID]")) == NominalType("CustomerID")


def test_parse_object() -> None:
    assert parse_type("Object") == ObjectType(properties=())
    person = ObjectType(
        properties=(
            PropertySpec("name", STRING, True),
            PropertySpec("email", STRING, False),
        )
    )
    assert person.render() == "Object{name: string, email?: string}"
    assert person.property("email") is not None
    assert person.property("missing") is None


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        "List[",
        "List[]",
        "List[string, integer]",  # List takes one parameter
        "Union[string]",  # Union needs two or more
        "Dict[string]",  # Dict needs two
        "string[integer]",  # primitives take no parameters
        "List string",  # missing bracket
        "List[string]]",  # unbalanced
        "List[string] extra",
        "123",
        "List[123]",
    ],
)
def test_malformed_type_expressions(bad: str) -> None:
    with pytest.raises(TypeParseError):
        parse_type(bad)


def test_error_includes_position() -> None:
    with pytest.raises(TypeParseError, match="position"):
        parse_type("List[string, integer]")


@pytest.mark.parametrize(
    "text",
    [
        "string",
        "CustomerID",
        "List[InvoiceID]",
        "Optional[CustomerID]",
        "Dict[string, integer]",
        "Union[CustomerID, InvoiceID]",
        "List[Dict[string, Optional[float]]]",
    ],
)
def test_render_roundtrip(text: str) -> None:
    assert parse_type(parse_type(text).render()) == parse_type(text)
