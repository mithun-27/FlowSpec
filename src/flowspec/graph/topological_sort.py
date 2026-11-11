"""Topological sorting of the workflow graph (pipeline P10 input).

Produces a valid execution order using Kahn's algorithm (O(V + E)).
The ready set is processed in sorted order, so the result is
deterministic: the same graph always yields the same order.

Cyclic graphs have no valid order. Cycles are diagnosed by
:mod:`flowspec.graph.cycle_detection` (E301/E104); this sort returns
``None`` rather than a partial or invented order — no fake results.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from flowspec.graph.graph import WorkflowGraph

__all__ = ["topological_sort"]


def topological_sort(graph: WorkflowGraph) -> list[str] | None:
    """A deterministic topological order of ``graph``, or ``None`` if cyclic."""
    in_degree = {step: graph.in_degree(step) for step in graph.step_ids}
    ready = sorted(step for step in graph.step_ids if in_degree[step] == 0)
    order: list[str] = []

    while ready:
        node = ready.pop(0)
        order.append(node)
        changed = False
        for successor in graph.successors(node):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                ready.append(successor)
                changed = True
        if changed:
            ready.sort()

    if len(order) != len(graph.step_ids):
        return None  # a cycle prevents any valid order (reported as E301/E104)
    return order
