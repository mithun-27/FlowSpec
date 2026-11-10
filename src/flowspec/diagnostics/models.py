"""The diagnostic data model.

``Diagnostic`` carries structured error information (code, severity,
category, message, workflow/step context, source location, expected and
received values, and correction suggestions) so that every compiler pass
reports failures uniformly instead of printing to the terminal.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["Diagnostic", "Severity"]


class Severity:
    """Planned severity levels for diagnostics: error, warning, info, hint."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"

    ALL = (ERROR, WARNING, INFO, HINT)


class Diagnostic:
    """Placeholder for a structured compiler diagnostic. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("Diagnostic is planned for v0.1.0; see docs/PROGRESS.md")
