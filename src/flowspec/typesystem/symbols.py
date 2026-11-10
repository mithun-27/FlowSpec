"""Symbol table for FlowSpec name resolution.

Tracks workflow inputs, tool definitions, step identifiers, tool output
fields, user-defined types, and workflow output references. Used to resolve
every expression and to report unknown tools, unknown steps, unknown output
properties, duplicate symbols, invalid forward references, and unresolved
variables. Declaration order must not matter — forward references are
permitted while the dependency graph stays valid.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["SymbolTable"]


class SymbolTable:
    """Placeholder for the symbol table. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("The symbol table is planned for v0.1.0; see docs/PROGRESS.md")
