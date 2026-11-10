"""Tool schema loading.

Loads tool definition files (``tools.yaml`` / ``tools.json``) into
``ToolDefinition`` objects, validating the registry structure and reporting
unknown type names and malformed schemas as structured diagnostics.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["load_tool_schema"]


def load_tool_schema(path: object) -> NoReturn:
    """Load a tool schema file into the registry. Not implemented yet."""
    raise NotImplementedError("Schema loading is planned for v0.1.0; see docs/PROGRESS.md")
