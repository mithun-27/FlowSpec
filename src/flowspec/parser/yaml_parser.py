"""Safe YAML loading for FlowSpec workflow and tool documents.

Loads YAML sources without unsafe object construction, enforces size and
nesting-depth limits against hostile input, and preserves line and column
information so later passes can attach source locations to diagnostics.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["parse_yaml"]


def parse_yaml(text: str) -> NoReturn:
    """Parse a YAML workflow or tool document. Not implemented yet."""
    raise NotImplementedError("YAML parsing is planned for v0.1.0; see docs/PROGRESS.md")
