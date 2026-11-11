"""Structured exception hierarchy for FlowSpec.

The compiler reports *workflow* problems as structured diagnostics, not
exceptions. Exceptions are reserved for conditions that are not about the
workflow itself: unreadable sources, malformed documents, invalid
configuration, and programming errors.

Mapping to diagnostic codes:

- :class:`SourceSyntaxError` → E001 (cannot be parsed at all)
- :class:`DocumentStructureError` → E002 (wrong shape)
- :class:`TypeParseError` → E205 (malformed type expression)
- :class:`ConfigurationError` → exit code 2 (project/config error)

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from flowspec.ast.nodes import SourceLocation

__all__ = [
    "ConfigurationError",
    "DocumentStructureError",
    "DuplicateToolError",
    "FlowSpecError",
    "InternalError",
    "SourceError",
    "SourceSyntaxError",
    "TypeParseError",
]


class FlowSpecError(Exception):
    """Base class for all FlowSpec-specific errors."""


class SourceError(FlowSpecError):
    """Base class for failures while reading or parsing a source document.

    Carries the diagnostic code the failure maps to and, when available,
    the source location where the failure was detected.
    """

    code: str = "E001"

    def __init__(self, message: str, location: SourceLocation | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.location = location


class SourceSyntaxError(SourceError):
    """A document cannot be parsed (E001): invalid YAML/JSON, duplicate keys,
    size or nesting-depth limit violations, or invalid expression syntax."""


class DocumentStructureError(SourceError):
    """A parsed document has the wrong structure (E002)."""

    code = "E002"


class TypeParseError(SourceError):
    """A type expression cannot be parsed (E205)."""

    code = "E205"


class ConfigurationError(FlowSpecError):
    """A FlowSpec project/configuration file is invalid (CLI exit code 2)."""


class DuplicateToolError(FlowSpecError):
    """A tool name was registered twice in the same registry."""


class InternalError(FlowSpecError):
    """An invariant was violated inside the compiler (CLI exit code 4)."""
