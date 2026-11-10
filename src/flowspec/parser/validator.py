"""Structural validation of parsed workflow and tool documents.

Validates that loaded YAML/JSON documents conform to the FlowSpec workflow
and tool schema shapes before AST construction, reporting E001/E002 syntax
and structure diagnostics with source locations.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["validate_document"]


def validate_document(document: object) -> NoReturn:
    """Validate the structure of a parsed workflow or tool document. Not implemented yet."""
    raise NotImplementedError("Document validation is planned for v0.1.0; see docs/PROGRESS.md")
