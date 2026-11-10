"""Expression type inference.

Infers the type of every expression from workflow input declarations, tool
input and output contracts, literal values, and previously resolved
expressions — deterministically, without any LLM involvement.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["infer_types"]


def infer_types(ast: object) -> NoReturn:
    """Infer the types of all expressions in an AST. Not implemented yet."""
    raise NotImplementedError("Type inference is planned for v0.1.0; see docs/PROGRESS.md")
