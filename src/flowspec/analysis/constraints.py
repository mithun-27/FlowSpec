"""Constraint validation engine.

Collects, normalizes, and deterministically evaluates constraints such as
``RequiredInput``, ``TypeCompatibility``, ``ReferenceExists``,
``DependencyExists``, ``DependencyAcyclic``, ``PermissionAvailable``,
``OutputExists``, and ``NonNullRequired``, attaching source locations and
generating diagnostics (E601).

Status: planned for v0.1.0 (deterministic rule-based evaluation); not
implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["ConstraintEngine"]


class ConstraintEngine:
    """Placeholder for the constraint validation engine. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError(
            "The constraint engine is planned for v0.1.0; see docs/PROGRESS.md"
        )
