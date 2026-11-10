"""Type expression parsing.

Parses textual type expressions — primitives, nominal names, and generic
constructions such as ``List[InvoiceID]`` or ``Optional[CustomerID]`` — into
internal type objects, with structured diagnostics for malformed or unknown
type expressions (E205).

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["parse_type"]


def parse_type(type_expr: object) -> NoReturn:
    """Parse a type expression into an internal type object. Not implemented yet."""
    raise NotImplementedError("Type parsing is planned for v0.1.0; see docs/PROGRESS.md")
