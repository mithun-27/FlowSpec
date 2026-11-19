"""Semantic analysis for FlowSpec workflows.

Submodules:

- ``name_resolution`` — resolving tools, references, and declarations.
- ``semantic_analyzer`` — validating declarations against their semantics.

Resolution is order-independent: steps may reference outputs declared
later in the file. Workflow problems such as unknown variables are
returned as E103 diagnostics, never raised as exceptions.

Status: implemented for the v0.1.0 compiler foundation; see
``docs/PROGRESS.md``.
"""
