"""Exporters for FlowSpec artifacts.

Exports compiled IR, analysis reports, and diagnostics in JSON and other
machine-readable formats with deterministic, stable serialization.

Status: planned for v0.1.0 (IR export); not implemented yet. See
``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["export_ir"]


def export_ir(result: object) -> NoReturn:
    """Export a compiled intermediate representation. Not implemented yet."""
    raise NotImplementedError("IR export is planned for v0.1.0; see docs/PROGRESS.md")
