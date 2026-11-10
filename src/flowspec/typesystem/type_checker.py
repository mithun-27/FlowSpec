"""Type compatibility checking.

Validates that source types are compatible with destination types using the
central compatibility rules (specification §6.5) — exact equality, nominal
distinctness, primitive widening, nullable handling, and strict-mode
``any`` policy. Compatibility logic is defined here and here only; it is
never spread across other compiler modules.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["TypeChecker"]


class TypeChecker:
    """Placeholder for the type compatibility checker. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("TypeChecker is planned for v0.1.0; see docs/PROGRESS.md")
