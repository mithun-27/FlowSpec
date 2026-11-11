"""The modular static analysis engine.

Independent analyzers, each returning structured diagnostics rather than
printing output. Submodules:

- ``static`` — analyzer orchestration and shared context.
- ``dataflow`` — tracking value origins (P9).
- ``constraints`` — deterministic constraint validation (P10).
- ``effects`` — side-effect analysis (P11).
- ``permissions`` — declared permission checking.
- ``suggestions`` — deterministic correction suggestions.

Status: ``static`` and ``constraints`` are implemented for the v0.1.0
compiler foundation; ``dataflow`` and ``effects`` are planned for
v0.2.0, ``permissions`` for v0.2.0, and ``suggestions`` for v0.4.0.
See ``docs/PROGRESS.md``.
"""
