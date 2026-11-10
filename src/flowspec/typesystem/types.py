"""Type definitions for the FlowSpec type system.

Planned type forms (specification §6):

- Primitives: ``string``, ``integer``, ``float``, ``boolean``, ``null``,
  ``any`` (the ``any`` type controlled by compiler configuration).
- Nominal types: user-defined identifiers such as ``CustomerID`` and
  ``InvoiceID`` that stay distinct even when they share an underlying
  representation (``CustomerID != InvoiceID``).
- Generic types: ``List[T]``, ``Dict[K, V]``, ``Optional[T]``,
  ``Union[A, B]``.
- Structural object types with nested, required, and optional properties.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["Type"]


class Type:
    """Placeholder base class for FlowSpec type objects. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("Type definitions are planned for v0.1.0; see docs/PROGRESS.md")
