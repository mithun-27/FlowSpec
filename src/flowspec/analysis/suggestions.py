"""Deterministic correction suggestions.

When a dependency is missing, searches registered tool outputs for
compatible producers, checks validity, reachability, cycle creation, and
permissions, and ranks candidates. Suggestions never modify the original
workflow. An LLM may optionally explain errors, but it is never part of
the trusted type-checking path.

Status: planned for v0.4.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["generate_suggestions"]


def generate_suggestions(diagnostic: object) -> NoReturn:
    """Generate ranked correction suggestions for a diagnostic. Not implemented yet."""
    raise NotImplementedError("Correction suggestions are planned for v0.4.0; see docs/PROGRESS.md")
