"""Deterministic type unification.

Determines whether two types can satisfy the same type constraint. The
initial version will support exact type equality, nominal type checking,
primitive widening (``integer`` → ``float``), generic type unification,
optional type handling, union types, and object compatibility.

Unification must stay deterministic — an LLM is never used for type
checking.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["unify"]


def unify(left: object, right: object) -> NoReturn:
    """Attempt to unify two types. Not implemented yet."""
    raise NotImplementedError("Type unification is planned for v0.1.0; see docs/PROGRESS.md")
