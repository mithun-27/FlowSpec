"""Structured compiler diagnostics.

Every diagnostic carries a code, severity, category, message, workflow and
step context, source location, expected/received values, and suggestions.
Submodules:

- ``models`` — the ``Diagnostic`` data model and severity levels.
- ``error_codes`` — the stable error code registry (E001-E701).
- ``formatter`` — human-readable rendering of diagnostics.

The core compiler must never depend on Rich; terminal formatting lives in
the CLI layer only.

Status: implemented for the v0.1.0 compiler foundation; see
``docs/PROGRESS.md``.
"""
