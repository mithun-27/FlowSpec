"""Deterministic type unification.

Determines whether two types can satisfy the same constraint, and if so,
the more general type they agree on. Unification is implemented as
bidirectional assignability through the central
:class:`~flowspec.typesystem.type_checker.TypeChecker` — v0.1.0 has no
type variables, so unification reduces to finding the least general type
both sides accept. An LLM is never used for type checking.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowspec.config import CompilerConfig
from flowspec.typesystem.type_checker import TypeChecker
from flowspec.typesystem.types import FLOAT, INTEGER, Type

__all__ = ["UnificationResult", "unify"]


@dataclass(frozen=True)
class UnificationResult:
    """The outcome of a unification attempt."""

    unified: bool
    type: Type | None = None


def unify(left: Type, right: Type, *, config: CompilerConfig | None = None) -> UnificationResult:
    """Can ``left`` and ``right`` satisfy the same constraint?

    On success, ``type`` is the more general of the two types (the target
    of the successful assignment direction). Integer and float unify to
    float.
    """
    if left == right:
        return UnificationResult(True, left)

    checker = TypeChecker(config)
    left_to_right = checker.check_assignment(left, right)
    if left_to_right.compatible:
        return UnificationResult(True, right)

    right_to_left = checker.check_assignment(right, left)
    if right_to_left.compatible:
        return UnificationResult(True, left)

    # integer and float unify to float even though only one direction is
    # directly assignable when parameters differ.
    if {left, right} == {INTEGER, FLOAT}:
        return UnificationResult(True, FLOAT)

    return UnificationResult(False)
