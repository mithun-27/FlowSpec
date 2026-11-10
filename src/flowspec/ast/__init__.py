"""Format-independent abstract syntax tree for FlowSpec workflows.

The AST represents parsed workflows independently of the source YAML/JSON
format. Submodules:

- ``nodes`` — base AST node definitions.
- ``workflow`` — workflow-level nodes (declarations, steps, outputs).
- ``expressions`` — expression nodes (references, literals).
- ``visitors`` — visitor protocol for compiler passes.

Status: planned for v0.1.0; see ``docs/PROGRESS.md``.
"""
