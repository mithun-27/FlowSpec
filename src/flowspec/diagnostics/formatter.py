"""Diagnostic formatting.

Renders structured diagnostics as plain text for terminal output and as
dictionaries for JSON export. The core compiler never depends on Rich;
this module produces plain strings, and the CLI layer may colorize them.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Iterable

from flowspec.diagnostics.models import Diagnostic, Severity

__all__ = ["format_diagnostic", "format_diagnostics", "format_summary"]

_SEVERITY_MARKS = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFO: "info",
    Severity.HINT: "hint",
}


def format_diagnostic(diagnostic: Diagnostic) -> str:
    """Render one diagnostic as a single human-readable line."""
    parts: list[str] = [f"{diagnostic.code}"]

    location = diagnostic.location
    if location is not None:
        parts.append(str(location))

    context = diagnostic.workflow or ""
    if diagnostic.step:
        context = f"{context}.{diagnostic.step}" if context else diagnostic.step
    if context:
        parts.append(f"({context})")

    parts.append(diagnostic.message)

    if diagnostic.expected is not None or diagnostic.received is not None:
        expected = diagnostic.expected if diagnostic.expected is not None else "?"
        received = diagnostic.received if diagnostic.received is not None else "?"
        parts.append(f"(expected {expected}, received {received})")

    line = " ".join(parts)

    for suggestion in diagnostic.suggestions:
        line += f"\n  suggestion: {suggestion}"

    return line


def format_diagnostics(diagnostics: Iterable[Diagnostic]) -> str:
    """Render many diagnostics, one per line, sorted by severity."""
    ordered = sorted(diagnostics, key=lambda d: (d.severity != Severity.ERROR, d.sort_key))
    return "\n".join(format_diagnostic(d) for d in ordered)


def format_summary(diagnostics: Iterable[Diagnostic]) -> str:
    """A one-line count summary, e.g. ``3 errors, 1 warning``."""
    errors = 0
    warnings = 0
    for diagnostic in diagnostics:
        if diagnostic.severity == Severity.ERROR:
            errors += 1
        elif diagnostic.severity == Severity.WARNING:
            warnings += 1
    chunks = []
    if errors:
        chunks.append(f"{errors} error{'s' if errors != 1 else ''}")
    if warnings:
        chunks.append(f"{warnings} warning{'s' if warnings != 1 else ''}")
    return ", ".join(chunks) if chunks else "no diagnostics"
