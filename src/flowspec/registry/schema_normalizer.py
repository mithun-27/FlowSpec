"""Schema normalization for imported tool definitions.

Normalizes external schemas (JSON Schema from MCP servers, OpenAPI
parameter and response schemas) into FlowSpec's internal type system,
mapping required fields, primitives, nested objects, and arrays, and
reporting — never silently ignoring — unsupported schema constructs.

Status: planned for v0.3.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["normalize_schema"]


def normalize_schema(schema: object) -> NoReturn:
    """Normalize an external schema into FlowSpec types. Not implemented yet."""
    raise NotImplementedError("Schema normalization is planned for v0.3.0; see docs/PROGRESS.md")
