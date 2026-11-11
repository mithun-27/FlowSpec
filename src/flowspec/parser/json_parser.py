"""JSON loading for FlowSpec workflow and tool documents.

Loads JSON with the same protections as the YAML parser — document size
and nesting-depth limits, and duplicate-key rejection — and reports line
and column positions for syntax errors from the standard decoder.

JSON documents do not carry per-value source locations in v0.1.0;
diagnostics fall back to workflow/step context. YAML is the primary
format and is fully located.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

import json
from typing import Any

from flowspec.ast.nodes import SourceLocation
from flowspec.exceptions import SourceSyntaxError
from flowspec.parser.document import Document, check_nesting_depth
from flowspec.parser.yaml_parser import DEFAULT_MAX_DEPTH, DEFAULT_MAX_SIZE

__all__ = ["parse_json", "parse_json_document"]


class _DuplicateKeyError(ValueError):
    """Raised by the object hook when a JSON object repeats a key."""

    def __init__(self, key: str) -> None:
        super().__init__(f"duplicate object key {key!r}")
        self.key = key


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def parse_json(
    text: str,
    *,
    file: str = "<string>",
    max_size: int = DEFAULT_MAX_SIZE,
) -> Any:
    """Parse a JSON document into plain Python data.

    Raises :class:`SourceSyntaxError` (E001) for invalid JSON, duplicate
    object keys, or documents exceeding the size limit.
    """
    if len(text) > max_size:
        raise SourceSyntaxError(
            f"document exceeds the maximum size of {max_size} characters",
            location=SourceLocation.unknown(file),
        )
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except _DuplicateKeyError as exc:
        raise SourceSyntaxError(
            f"invalid JSON: {exc}", location=SourceLocation.unknown(file)
        ) from exc
    except json.JSONDecodeError as exc:
        raise SourceSyntaxError(
            f"invalid JSON: {exc.msg}",
            location=SourceLocation(file=file, line=exc.lineno, column=exc.colno),
        ) from exc
    except ValueError as exc:  # e.g. NaN handling changes across versions
        raise SourceSyntaxError(
            f"invalid JSON: {exc}", location=SourceLocation.unknown(file)
        ) from exc


def parse_json_document(
    text: str,
    *,
    file: str = "<string>",
    max_size: int = DEFAULT_MAX_SIZE,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> Document:
    """Parse JSON into a :class:`Document` (without per-value locations)."""
    data = parse_json(text, file=file, max_size=max_size)
    check_nesting_depth(data, max_depth=max_depth, file=file)
    return Document(data=data, file=file, locations={}, format="json")
