"""Tests for deterministic type unification."""

from __future__ import annotations

from flowspec.typesystem.types import (
    FLOAT,
    INTEGER,
    STRING,
    GenericType,
    NominalType,
)
from flowspec.typesystem.unification import unify


def test_identical_types_unify() -> None:
    result = unify(STRING, STRING)
    assert result.unified and result.type == STRING


def test_integer_and_float_unify_to_float() -> None:
    result = unify(INTEGER, FLOAT)
    assert result.unified and result.type == FLOAT
    result = unify(FLOAT, INTEGER)
    assert result.unified and result.type == FLOAT


def test_assignable_directions_unify_to_target() -> None:
    optional = GenericType("Optional", (STRING,))
    result = unify(STRING, optional)
    assert result.unified and result.type == optional


def test_distinct_nominals_do_not_unify() -> None:
    result = unify(NominalType("CustomerID"), NominalType("InvoiceID"))
    assert not result.unified
    assert result.type is None


def test_incompatible_primitives_do_not_unify() -> None:
    assert not unify(STRING, INTEGER).unified
