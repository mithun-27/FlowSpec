"""The modular static analysis engine.

Independent analyzers, each returning structured diagnostics rather than
printing output. Submodules:

- ``static`` — analyzer orchestration and shared context.
- ``dataflow`` — tracking value origins (P9).
- ``constraints`` — deterministic constraint validation (P10).
- ``effects`` — side-effect analysis (P11).
- ``permissions`` — declared permission checking.
- ``suggestions`` — deterministic correction suggestions.

Status: planned for v0.1.0 (core analyzers) and v0.2.0 (advanced); see
``docs/PROGRESS.md``.
"""
