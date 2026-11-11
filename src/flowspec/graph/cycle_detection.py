"""Circular dependency detection (pipeline P8).

Detects cycles in the workflow dependency graph with an iterative
Tarjan strongly-connected-components pass — O(V + E), and no recursion,
so hostile deeply-chained workflows cannot hit the interpreter recursion
limit.

- A cycle of two or more steps is E301 (circular dependency), reported
  with the cycle path.
- A step consuming its own output is a cycle of one: E104
  (self-dependency).

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Diagnostic, Severity
from flowspec.graph.graph import WorkflowGraph

__all__ = ["Cycle", "cycle_diagnostics", "detect_cycles"]


@dataclass(frozen=True)
class Cycle:
    """A detected dependency cycle.

    ``steps`` is the cycle path in dependency order, starting and ending
    with the same step for self-dependencies.
    """

    kind: str  # "self" or "circular"
    steps: tuple[str, ...]

    @property
    def path(self) -> str:
        return " -> ".join(self.steps)


def detect_cycles(graph: WorkflowGraph) -> list[Cycle]:
    """Every dependency cycle in ``graph``, deterministically ordered."""
    cycles: list[Cycle] = []
    for scc in _strongly_connected_components(graph):
        if len(scc) == 1:
            node = scc[0]
            if node in graph.successors(node):
                cycles.append(Cycle(kind="self", steps=(node, node)))
        else:
            cycles.append(Cycle(kind="circular", steps=tuple(_cycle_path(set(scc), graph))))
    return cycles


def cycle_diagnostics(
    graph: WorkflowGraph,
    workflow: str | None = None,
) -> list[Diagnostic]:
    """Diagnostics for every cycle in ``graph`` (E301 / E104)."""
    diagnostics: list[Diagnostic] = []
    for cycle in detect_cycles(graph):
        if cycle.kind == "self":
            node = cycle.steps[0]
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.INVALID_DEPENDENCY,
                    severity=Severity.ERROR,
                    message=f"step {node!r} consumes its own output (self-dependency)",
                    workflow=workflow,
                    step=node,
                    suggestions=(f"reference an output of a different step in {node!r}",),
                )
            )
        else:
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.CIRCULAR_DEPENDENCY,
                    severity=Severity.ERROR,
                    message=f"circular dependency: {cycle.path}",
                    workflow=workflow,
                    suggestions=("break the cycle by removing one dependency",),
                )
            )
    return diagnostics


def _strongly_connected_components(graph: WorkflowGraph) -> list[list[str]]:
    """Iterative Tarjan SCC over the graph, in deterministic order."""
    index = 0
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    sccs: list[list[str]] = []

    for root in graph.step_ids:
        if root in indices:
            continue
        work: list[tuple[str, Iterator[str]]] = [(root, iter(graph.successors(root)))]
        indices[root] = lowlink[root] = index
        index += 1
        stack.append(root)
        on_stack.add(root)

        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in indices:
                    indices[child] = lowlink[child] = index
                    index += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(graph.successors(child))))
                    advanced = True
                    break
                if child in on_stack:
                    lowlink[node] = min(lowlink[node], indices[child])
            if advanced:
                continue

            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])
            if lowlink[node] == indices[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                sccs.append(sorted(component))
    return sccs


def _cycle_path(scc: set[str], graph: WorkflowGraph) -> list[str]:
    """A concrete cycle path within a strongly connected component.

    Walks smallest-name successors restricted to the component until a
    node repeats; the component is strongly connected, so a repeat is
    guaranteed.
    """
    start = min(scc)
    path = [start]
    seen = {start}
    current = start
    while True:
        candidates = [step for step in graph.successors(current) if step in scc]
        next_step = min(candidates)  # strongly connected → non-empty
        if next_step in seen:
            first = path.index(next_step)
            return [*path[first:], next_step]
        path.append(next_step)
        seen.add(next_step)
        current = next_step
