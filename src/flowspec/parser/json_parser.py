"""JSON loading for FlowSpec workflow and tool documents.

Loads JSON sources with the same size and nesting-depth protections as the
YAML parser and preserves position information for diagnostics.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["parse_json"]


def parse_json(text: str) -> NoReturn:
    """Parse a JSON workflow or tool document. Not implemented yet."""
    raise NotImplementedError("JSON parsing is planned for v0.1.0; see docs/PROGRESS.md")
