"""The versioned FlowSpec intermediate representation.

A stable, format-independent IR carrying the workflow name and status,
explicit input and output types, step dependencies, tool metadata, effect
and permission metadata, execution stages, compiler version, and source
metadata. Serialization is deterministic: identical inputs and
configuration produce equivalent IR. Invalid workflows are never exported
as executable IR.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["IntermediateRepresentation"]


class IntermediateRepresentation:
    """Placeholder for the compiled intermediate representation. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError(
            "IntermediateRepresentation is planned for v0.1.0; see docs/PROGRESS.md"
        )
