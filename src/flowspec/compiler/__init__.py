"""The FlowSpec compiler pipeline.

Submodules:

- ``compiler`` — the ``Compiler`` facade (parsing, analysis, compilation).
- ``pipeline`` — orchestration of the P0-P12 compilation passes.
- ``ir`` — the versioned FlowSpec intermediate representation.
- ``result`` — ``CompilationResult`` carrying IR and/or diagnostics.

Compilation never executes tools; only an explicit runtime invocation may.

Status: implemented for the v0.1.0 compiler foundation; see
``docs/PROGRESS.md``.
"""
