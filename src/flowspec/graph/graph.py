"""The workflow dependency graph (pipeline P7).

A directed graph over workflow steps using adjacency lists and reverse
adjacency lists. Edges retain source step, destination step, source
output, destination input, and source location — everything later passes
need for diagnostics and scheduling.

Determinism: step ids keep declaration order; adjacency queries return
sorted tuples; the serialized form sorts edges, so two compilations of
the same workflow always produce identical graphs.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Iterable

from flowspec.ast.workflow import WorkflowNode
from flowspec.graph.dependency import DependencyEdge, extract_dependencies
from flowspec.typesystem.symbols import SymbolTable

__all__ = ["WorkflowGraph"]


class WorkflowGraph:
    """A directed dependency graph over the steps of one workflow."""

    def __init__(self, steps: Iterable[str], edges: Iterable[DependencyEdge]) -> None:
        # Declaration order, first occurrence only (duplicates are E304).
        seen: set[str] = set()
        ordered: list[str] = []
        for step_id in steps:
            if step_id not in seen:
                seen.add(step_id)
                ordered.append(step_id)

        self._steps: tuple[str, ...] = tuple(ordered)
        self._edges: tuple[DependencyEdge, ...] = tuple(edges)
        self._successors: dict[str, set[str]] = {step: set() for step in self._steps}
        self._predecessors: dict[str, set[str]] = {step: set() for step in self._steps}
        for edge in self._edges:
            if edge.from_step in self._successors and edge.to_step in self._successors:
                self._successors[edge.from_step].add(edge.to_step)
                self._predecessors[edge.to_step].add(edge.from_step)

    @classmethod
    def from_workflow(cls, workflow: WorkflowNode, symbols: SymbolTable) -> WorkflowGraph:
        """Build the graph of a resolved workflow."""
        return cls(workflow.step_ids, extract_dependencies(workflow, symbols))

    @property
    def step_ids(self) -> tuple[str, ...]:
        """All step ids in declaration order."""
        return self._steps

    @property
    def edges(self) -> tuple[DependencyEdge, ...]:
        """All dependency edges in source order."""
        return self._edges

    def __len__(self) -> int:
        return len(self._steps)

    def __contains__(self, step_id: object) -> bool:
        return isinstance(step_id, str) and step_id in self._successors

    def has_step(self, step_id: str) -> bool:
        return step_id in self._successors

    def successors(self, step_id: str) -> tuple[str, ...]:
        """The steps that depend on ``step_id``, sorted."""
        return tuple(sorted(self._successors.get(step_id, ())))

    def predecessors(self, step_id: str) -> tuple[str, ...]:
        """The steps ``step_id`` depends on, sorted."""
        return tuple(sorted(self._predecessors.get(step_id, ())))

    def in_degree(self, step_id: str) -> int:
        """The number of distinct steps ``step_id`` depends on."""
        return len(self._predecessors.get(step_id, ()))

    def out_degree(self, step_id: str) -> int:
        """The number of distinct steps that depend on ``step_id``."""
        return len(self._successors.get(step_id, ()))

    def has_edge(self, from_step: str, to_step: str) -> bool:
        return to_step in self._successors.get(from_step, set())

    def to_dict(self) -> dict[str, object]:
        """A deterministic JSON-friendly representation."""
        return {
            "steps": list(self._steps),
            "edges": [
                {
                    "from_step": edge.from_step,
                    "to_step": edge.to_step,
                    "output": edge.output,
                    "argument": edge.argument,
                }
                for edge in sorted(
                    self._edges, key=lambda e: (e.from_step, e.to_step, e.argument, e.output)
                )
            ],
            "adjacency": {step: list(self.successors(step)) for step in self._steps},
        }
