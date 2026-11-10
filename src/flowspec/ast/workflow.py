"""Workflow-level AST nodes.

Planned nodes: ``WorkflowNode`` (name, inputs, steps, outputs),
``WorkflowInputNode``, ``ToolCallNode``, and ``OutputNode`` — the structural
backbone of a parsed workflow.

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["WorkflowNode"]


class WorkflowNode:
    """Placeholder for the root workflow AST node. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("WorkflowNode is planned for v0.1.0; see docs/PROGRESS.md")
