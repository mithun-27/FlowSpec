"""Diagnostic formatting.

Renders structured diagnostics for human-readable terminal output, JSON
diagnostics, and machine-readable streams, including source file, line,
and column where available. Rich is used only by the CLI layer — the core
compiler never depends on it.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["format_diagnostic"]


def format_diagnostic(diagnostic: object) -> NoReturn:
    """Render a structured diagnostic for output. Not implemented yet."""
    raise NotImplementedError("Diagnostic formatting is planned for v0.1.0; see docs/PROGRESS.md")
