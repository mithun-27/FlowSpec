"""AST construction from parsed workflow documents.

Transforms validated YAML/JSON documents into the format-independent AST
defined in :mod:`flowspec.ast`, preserving identifiers, values, and source
locations.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["build_ast"]


def build_ast(document: object) -> NoReturn:
    """Build an AST from a parsed and validated document. Not implemented yet."""
    raise NotImplementedError("AST construction is planned for v0.1.0; see docs/PROGRESS.md")
