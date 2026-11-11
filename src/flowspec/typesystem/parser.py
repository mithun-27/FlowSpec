"""Type expression parsing.

Parses textual type expressions — primitives, nominal names, and generic
constructions such as ``List[InvoiceID]``, ``Optional[CustomerID]``,
``Dict[string, integer]``, and ``Union[A, B]`` — into internal type
objects. Malformed expressions raise :class:`TypeParseError` (E205) with
the position of the failure.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from flowspec.exceptions import TypeParseError
from flowspec.typesystem.types import (
    GENERIC_BASES,
    PRIMITIVES,
    GenericType,
    NominalType,
    ObjectType,
    PrimitiveType,
    Type,
)

__all__ = ["parse_type"]

_NAME_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_NAME_CHARS = _NAME_START | set("0123456789")


class _TypeParser:
    """A small recursive-descent parser for type expressions."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def error(self, message: str) -> TypeParseError:
        return TypeParseError(f"{message} at position {self.pos} of {self.text!r}")

    def skip_whitespace(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def peek(self) -> str | None:
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def parse(self) -> Type:
        self.skip_whitespace()
        type_ = self.parse_type()
        self.skip_whitespace()
        if self.pos != len(self.text):
            raise self.error(f"unexpected {self.text[self.pos]!r}")
        return type_

    def parse_type(self) -> Type:
        self.skip_whitespace()
        name = self.parse_name()
        self.skip_whitespace()

        if self.peek() != "[":
            return self.simple_type(name)

        self.pos += 1  # consume '['
        parameters: list[Type] = []
        self.skip_whitespace()
        if self.peek() == "]":
            raise self.error(f"generic type {name!r} requires at least one parameter")
        while True:
            parameters.append(self.parse_type())
            self.skip_whitespace()
            char = self.peek()
            if char == ",":
                self.pos += 1
                continue
            if char == "]":
                self.pos += 1
                break
            raise self.error(f"expected ',' or ']' in parameters of {name!r}")

        if name not in GENERIC_BASES:
            raise self.error(f"{name!r} does not take type parameters")
        if name == "Union":
            if len(parameters) < 2:
                raise self.error("Union requires at least two type parameters")
        elif len(parameters) != GENERIC_BASES[name]:
            expected = GENERIC_BASES[name]
            raise self.error(
                f"{name} takes exactly {expected} type parameter"
                f"{'s' if expected != 1 else ''}, received {len(parameters)}"
            )

        return GenericType(base=name, parameters=tuple(parameters))

    def parse_name(self) -> str:
        self.skip_whitespace()
        start = self.pos
        if self.pos >= len(self.text) or self.text[self.pos] not in _NAME_START:
            raise self.error("expected a type name")
        while self.pos < len(self.text) and self.text[self.pos] in _NAME_CHARS:
            self.pos += 1
        return self.text[start : self.pos]

    def simple_type(self, name: str) -> Type:
        if name in PRIMITIVES:
            return PrimitiveType(name)
        if name == "Object":
            return ObjectType(properties=())
        if name in GENERIC_BASES:
            raise self.error(f"generic type {name!r} requires type parameters")
        return NominalType(name)


def parse_type(expr: str) -> Type:
    """Parse a type expression into an internal type object.

    Raises :class:`TypeParseError` (E205) for malformed expressions.
    """
    if not isinstance(expr, str) or not expr.strip():
        raise TypeParseError(f"type expression must be a non-empty string, received {expr!r}")
    return _TypeParser(expr).parse()
