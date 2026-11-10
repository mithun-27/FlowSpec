"""The FlowSpec tool registry.

Tracks tool definitions with explicit input and output contracts,
descriptions, effects, permissions, and nullability declarations. Unknown
tool references in workflows are reported against this registry (E401).

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["ToolRegistry"]


class ToolRegistry:
    """Placeholder for the tool registry. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("ToolRegistry is planned for v0.1.0; see docs/PROGRESS.md")
