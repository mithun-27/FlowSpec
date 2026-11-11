"""Parsed documents with source-location lookup.

A :class:`Document` pairs the plain Python data produced by the YAML/JSON
parsers with a lookup table from container objects (mappings and
sequences) to their source locations, so later passes can attach precise
positions to diagnostics.

Location keys use :func:`id` of the container objects inside
``Document.data``; the document (and therefore its object tree) must stay
alive while locations are looked up — the compiler keeps the document
referenced for the whole pipeline run.

Limitation: JSON documents carry no per-value positions in v0.1.0, so
``locate`` returns ``None`` for them and diagnostics fall back to
workflow/step context. YAML is the primary format and is fully located.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from flowspec.ast.nodes import SourceLocation
from flowspec.exceptions import SourceSyntaxError

__all__ = ["Document", "check_nesting_depth"]

_SEQUENCE_TYPES = (list, tuple)


@dataclass
class Document:
    """A parsed source document plus a container→location map."""

    data: Any
    file: str
    locations: dict[int, SourceLocation] = field(default_factory=dict)
    format: str = "yaml"

    def locate(self, obj: Any) -> SourceLocation | None:
        """The source location of ``obj`` if it is a located container."""
        return self.locations.get(id(obj))

    def located(self, obj: Any) -> SourceLocation:
        """The location of ``obj`` or the best available fallback."""
        return self.locate(obj) or SourceLocation.unknown(self.file)


def check_nesting_depth(value: Any, *, max_depth: int, file: str) -> None:
    """Reject documents nested deeper than ``max_depth`` (E001).

    Uses an iterative walk so hostile deeply-nested input cannot hit the
    interpreter recursion limit.
    """
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            raise SourceSyntaxError(
                f"document nesting exceeds the maximum depth of {max_depth}",
                location=SourceLocation.unknown(file),
            )
        if isinstance(current, dict):
            stack.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, _SEQUENCE_TYPES):
            stack.extend((child, depth + 1) for child in current)


def iter_mapping_items(value: Any) -> Iterator[tuple[str, Any]]:
    """Yield ``(key, child)`` pairs if ``value`` is a mapping, else nothing."""
    if isinstance(value, dict):
        yield from value.items()
