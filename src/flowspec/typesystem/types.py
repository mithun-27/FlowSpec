"""Type definitions for the FlowSpec type system.

Type forms (specification §6):

- Primitives: ``string``, ``integer``, ``float``, ``boolean``, ``null``,
  ``any`` (the ``any`` type is controlled by compiler configuration).
- Nominal types: user-defined identifiers such as ``CustomerID`` that stay
  distinct even when they share an underlying representation.
- Generic types: ``List[T]``, ``Optional[T]``, ``Union[A, B]``,
  ``Dict[K, V]``.
- Structural object types with nested, required, and optional properties.

Types are frozen and hashable; structural equality is exact.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ANY",
    "BOOLEAN",
    "FLOAT",
    "GENERIC_BASES",
    "INTEGER",
    "NULL",
    "PRIMITIVES",
    "STRING",
    "GenericType",
    "NominalType",
    "ObjectType",
    "PrimitiveType",
    "PropertySpec",
    "Type",
    "is_any",
    "is_null",
    "is_optional",
    "optional_of",
]

PRIMITIVES = ("string", "integer", "float", "boolean", "null", "any")

#: Generic base names mapped to the number of type parameters they take.
#: ``Union`` takes two or more.
GENERIC_BASES = {"List": 1, "Optional": 1, "Dict": 2, "Union": 2}


@dataclass(frozen=True)
class Type:
    """Base class for all FlowSpec types."""

    def render(self) -> str:
        """The canonical source form of this type."""
        raise NotImplementedError  # pragma: no cover - abstract


@dataclass(frozen=True)
class PrimitiveType(Type):
    """A built-in primitive type."""

    name: str

    def render(self) -> str:
        return self.name


@dataclass(frozen=True)
class NominalType(Type):
    """A user-defined nominal type, e.g. ``CustomerID``.

    Nominal types with different names are never interchangeable, even
    when their underlying representation is identical.
    """

    name: str

    def render(self) -> str:
        return self.name


@dataclass(frozen=True)
class GenericType(Type):
    """A parameterized type: ``List[T]``, ``Optional[T]``, ``Union[...]``,
    ``Dict[K, V]``."""

    base: str
    parameters: tuple[Type, ...]

    def render(self) -> str:
        return f"{self.base}[{', '.join(parameter.render() for parameter in self.parameters)}]"


@dataclass(frozen=True)
class PropertySpec:
    """One property of a structural object type."""

    name: str
    type: Type
    required: bool


@dataclass(frozen=True)
class ObjectType(Type):
    """A structural object type with nested properties."""

    properties: tuple[PropertySpec, ...]

    def render(self) -> str:
        if not self.properties:
            return "Object"
        rendered = ", ".join(
            f"{property.name}{'?' if not property.required else ''}: {property.type.render()}"
            for property in self.properties
        )
        return f"Object{{{rendered}}}"

    def property(self, name: str) -> PropertySpec | None:
        """The property with ``name``, if declared."""
        for candidate in self.properties:
            if candidate.name == name:
                return candidate
        return None


# Frequently used singletons.
STRING = PrimitiveType("string")
INTEGER = PrimitiveType("integer")
FLOAT = PrimitiveType("float")
BOOLEAN = PrimitiveType("boolean")
NULL = PrimitiveType("null")
ANY = PrimitiveType("any")


def is_optional(type_: Type) -> bool:
    """Whether ``type_`` is ``Optional[T]``."""
    return isinstance(type_, GenericType) and type_.base == "Optional"


def optional_of(type_: Type) -> Type:
    """The ``T`` in ``Optional[T]`` (identity for anything else)."""
    if isinstance(type_, GenericType) and type_.base == "Optional":
        return type_.parameters[0]
    return type_


def is_any(type_: Type) -> bool:
    """Whether ``type_`` is the ``any`` primitive."""
    return isinstance(type_, PrimitiveType) and type_.name == "any"


def is_null(type_: Type) -> bool:
    """Whether ``type_`` is the ``null`` primitive."""
    return isinstance(type_, PrimitiveType) and type_.name == "null"
