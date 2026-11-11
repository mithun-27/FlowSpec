"""Tests for the central type compatibility rules (specification §6.5)."""

from __future__ import annotations

from flowspec.config import CompilerConfig
from flowspec.typesystem.type_checker import TypeChecker
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
    PropertySpec,
)

CHECKER = TypeChecker()


def _ok(source, target) -> None:
    result = CHECKER.check_assignment(source, target)
    assert result.compatible, result.reason


def _fail(source, target, code: str) -> None:
    result = CHECKER.check_assignment(source, target)
    assert not result.compatible
    assert result.code == code, result.reason


def test_primitive_rules() -> None:
    _ok(STRING, STRING)
    _ok(INTEGER, INTEGER)
    _ok(INTEGER, FLOAT)  # widening
    _fail(FLOAT, INTEGER, "E201")
    _fail(STRING, INTEGER, "E201")
    _fail(INTEGER, STRING, "E201")
    _fail(BOOLEAN, STRING, "E201")


def test_nominal_rules() -> None:
    customer = NominalType("CustomerID")
    invoice = NominalType("InvoiceID")
    _ok(customer, customer)
    _fail(customer, invoice, "E202")
    _fail(invoice, customer, "E202")
    _fail(STRING, customer, "E201")
    _fail(customer, STRING, "E201")


def test_nullable_rules() -> None:
    optional_string = GenericType("Optional", (STRING,))
    _ok(NULL, optional_string)
    _fail(NULL, STRING, "E204")
    _fail(optional_string, STRING, "E204")
    _ok(STRING, optional_string)
    _ok(optional_string, optional_string)
    _fail(
        GenericType("Optional", (INTEGER,)),
        GenericType("Optional", (STRING,)),
        "E201",
    )


def test_any_policy() -> None:
    _fail(ANY, STRING, "E203")
    _fail(STRING, ANY, "E203")

    permissive = TypeChecker(CompilerConfig(strict_types=False))
    assert permissive.check_assignment(ANY, STRING).compatible
    assert permissive.check_assignment(STRING, ANY).compatible

    allowed = TypeChecker(CompilerConfig(allow_unknown_types=True))
    assert allowed.check_assignment(ANY, STRING).compatible


def test_generic_rules() -> None:
    _ok(
        GenericType("List", (STRING,)),
        GenericType("List", (STRING,)),
    )
    _fail(
        GenericType("List", (STRING,)),
        GenericType("List", (INTEGER,)),
        "E201",
    )
    _ok(
        GenericType("List", (INTEGER,)),
        GenericType("List", (FLOAT,)),  # element widening
    )
    _fail(
        GenericType("List", (STRING,)),
        GenericType("Dict", (STRING, STRING)),
        "E201",
    )
    _ok(
        GenericType("Dict", (STRING, INTEGER)),
        GenericType("Dict", (STRING, INTEGER)),
    )


def test_union_rules() -> None:
    union = GenericType("Union", (STRING, INTEGER))
    _ok(STRING, union)
    _ok(INTEGER, union)
    _fail(BOOLEAN, union, "E201")
    _ok(GenericType("Union", (INTEGER, FLOAT)), FLOAT)  # every member widens
    _fail(union, STRING, "E201")
    _ok(union, GenericType("Union", (INTEGER, STRING, BOOLEAN)))


def test_object_rules() -> None:
    source = ObjectType((PropertySpec("name", STRING, True),))
    exact = ObjectType((PropertySpec("name", STRING, True),))
    _ok(source, exact)
    # Extra source properties are fine (width subtyping).
    wider = ObjectType((PropertySpec("name", STRING, True), PropertySpec("email", STRING, True)))
    _ok(wider, exact)
    # Missing required target property.
    _fail(
        source,
        ObjectType((PropertySpec("name", STRING, True), PropertySpec("id", INTEGER, True))),
        "E201",
    )
    # Optional target property may be absent.
    _ok(
        source,
        ObjectType((PropertySpec("name", STRING, True), PropertySpec("id", INTEGER, False))),
    )
    # Wrong property type.
    _fail(
        source,
        ObjectType((PropertySpec("name", INTEGER, True),)),
        "E201",
    )
    _fail(source, STRING, "E201")


def test_null_target_only_accepts_null() -> None:
    _fail(STRING, NULL, "E201")


def test_failure_code_defaults_to_e201() -> None:
    result = CHECKER.check_assignment(STRING, INTEGER)
    assert result.failure_code == "E201"
