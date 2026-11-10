"""Dependency graph rendering.

Renders workflow dependency graphs for the ``flowspec graph`` command and
the Playground, using Graphviz with the Graphviz ``viz`` extra.

Status: planned for v0.4.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

from typing import NoReturn

__all__ = ["render_graph"]


def render_graph(graph: object) -> NoReturn:
    """Render a workflow dependency graph. Not implemented yet."""
    raise NotImplementedError("Graph rendering is planned for v0.4.0; see docs/PROGRESS.md")
