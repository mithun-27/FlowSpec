"""The FlowSpec compiler facade.

The ``Compiler`` class is the main public entry point: it loads tool
registries, parses workflows, runs the full pass pipeline, and returns a
``CompilationResult`` containing either executable IR plus an execution plan
(valid workflows) or structured diagnostics (invalid workflows). Invalid
workflows never produce executable IR.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["Compiler"]


class Compiler:
    """Placeholder for the FlowSpec compiler facade. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("Compiler is planned for v0.1.0; see docs/PROGRESS.md")
