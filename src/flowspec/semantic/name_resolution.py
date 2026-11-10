"""Name resolution for FlowSpec workflows.

Resolves tool references against the registry and data references
(``$input.*`` and ``$step.*``) against the symbol table, reporting unknown
tools (E401), unknown output references (E102), and unresolved variables
(E103). Resolution is order-independent — forward references are allowed as
long as the dependency graph remains valid.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["NameResolver"]


class NameResolver:
    """Placeholder for the workflow name resolver. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("NameResolver is planned for v0.1.0; see docs/PROGRESS.md")
