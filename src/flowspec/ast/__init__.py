"""Workflow language AST — the format-independent representation of FlowSpec workflows.

The AST represents parsed workflows independently of the source YAML/JSON
format. Submodules:

- ``nodes`` — base AST node definitions.
- ``workflow`` — workflow-level nodes (declarations, steps, outputs).
- ``expressions`` — expression nodes (references, literals).
- ``visitors`` — visitor protocol for compiler passes.

Nodes are frozen dataclasses carrying a ``SourceLocation`` (file, 1-based
line and column), so diagnostics can point back to the source text. Passes
read the AST; they must not mutate it.

Status: implemented for the v0.1.0 compiler foundation; see
``docs/PROGRESS.md``.
"""
