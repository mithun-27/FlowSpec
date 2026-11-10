"""Tool execution adapters.

Dispatch compiled workflow steps to concrete backends — MCP servers, REST
APIs, and Python functions. Adapters validate actual tool responses
against declared output contracts at runtime (a future capability) and
enforce security policies independently of the compiler.

Status: planned; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["ToolAdapter"]


class ToolAdapter:
    """Placeholder base class for tool execution adapters. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("ToolAdapter is planned; see docs/PROGRESS.md")
