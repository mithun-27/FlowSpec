"""The diagnostic data model.

Every compiler pass reports failures as :class:`Diagnostic` records —
structured data carrying a code, severity, message, workflow/step context,
source location, expected/received values, and suggestions. The core
compiler never depends on terminal formatting libraries; rendering lives
in :mod:`flowspec.diagnostics.formatter` and the CLI.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from flowspec.ast.nodes import SourceLocation
from flowspec.diagnostics.error_codes import ErrorCodes

__all__ = ["Diagnostic", "Severity", "dedupe_diagnostics", "sort_diagnostics"]


class Severity:
    """Diagnostic severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"

    ALL = (ERROR, WARNING, INFO, HINT)


@dataclass(frozen=True)
class Diagnostic:
    """A structured compiler diagnostic.

    ``category`` is derived from ``code`` through the error code registry.
    Diagnostics are frozen and hashable so they can be deduplicated.
    """

    code: str
    severity: str
    message: str
    workflow: str | None = None
    step: str | None = None
    location: SourceLocation | None = None
    expected: str | None = None
    received: str | None = None
    suggestions: tuple[str, ...] = ()

    @property
    def category(self) -> str:
        """The registry category of this diagnostic's code."""
        return ErrorCodes.category(self.code)

    @property
    def is_error(self) -> bool:
        """Whether this diagnostic blocks compilation."""
        return self.severity == Severity.ERROR

    @property
    def sort_key(self) -> tuple[str, str, int, int, str, str]:
        """A deterministic ordering key: code, then location, then message."""
        location = self.location
        file = location.file if location else ""
        line = location.line if location else 0
        column = location.column if location else 0
        return (self.code, file, line, column, self.message, self.step or "")

    @property
    def dedupe_key(self) -> tuple[str, str, int, int, str, str, str]:
        """Identity used when aggregating across passes."""
        return (*self.sort_key, self.severity)

    def to_dict(self) -> dict[str, object]:
        """A JSON-friendly representation."""
        return {
            "code": self.code,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "workflow": self.workflow,
            "step": self.step,
            "location": (
                {
                    "file": self.location.file,
                    "line": self.location.line,
                    "column": self.location.column,
                }
                if self.location
                else None
            ),
            "expected": self.expected,
            "received": self.received,
            "suggestions": list(self.suggestions),
        }


@dataclass
class DiagnosticCollection:
    """An accumulating, deduplicating, deterministic diagnostic sink."""

    diagnostics: list[Diagnostic] = field(default_factory=list)
    _seen: dict[tuple[str, str, int, int, str, str, str], Diagnostic] = field(default_factory=dict)

    def add(self, diagnostic: Diagnostic) -> None:
        """Add a diagnostic, ignoring exact duplicates."""
        if diagnostic.dedupe_key not in self._seen:
            self._seen[diagnostic.dedupe_key] = diagnostic
            self.diagnostics.append(diagnostic)

    def extend(self, diagnostics: Iterable[Diagnostic]) -> None:
        """Add each diagnostic in ``diagnostics``."""
        for diagnostic in diagnostics:
            self.add(diagnostic)

    @property
    def has_errors(self) -> bool:
        """Whether any diagnostic blocks compilation."""
        return any(d.is_error for d in self.diagnostics)

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.is_error)

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.WARNING)

    def sorted(self) -> list[Diagnostic]:
        """The diagnostics in deterministic order."""
        return sorted(self.diagnostics, key=lambda d: d.sort_key)


def sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> list[Diagnostic]:
    """Sort diagnostics into the canonical deterministic order."""
    return sorted(diagnostics, key=lambda d: d.sort_key)


def dedupe_diagnostics(diagnostics: Iterable[Diagnostic]) -> list[Diagnostic]:
    """Remove exact duplicates while preserving first-seen order."""
    collection = DiagnosticCollection()
    collection.extend(diagnostics)
    return collection.diagnostics
