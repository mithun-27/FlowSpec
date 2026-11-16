"""Workflow source parsing and AST construction.

Submodules:

- ``yaml_parser`` — safe YAML loading for workflow and tool documents.
- ``json_parser`` — JSON loading for workflow and tool documents.
- ``validator`` — structural validation of parsed documents.
- ``ast_builder`` — construction of the format-independent AST.

Both loaders use safe parsing with size and depth limits: workflow and
tool documents are untrusted input, so no arbitrary Python objects are
constructed from them. The AST that reaches later passes is the same
regardless of whether the source was YAML or JSON.

Status: implemented for the v0.1.0 compiler foundation; see
``docs/PROGRESS.md``.
"""
