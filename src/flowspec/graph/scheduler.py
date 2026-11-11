"""Parallel execution stage scheduling (pipeline P10).

Groups independent steps into execution stages using level-based Kahn
scheduling: stage *n* contains every step whose dependencies are all
satisfied by stages ``0..n-1``. Steps within a stage are sorted, so
scheduling is deterministic.

Cyclic graphs have no schedule: ``None`` is returned rather than a
partial plan. Stages never violate dependency constraints — a step only
runs after every step it consumes has completed.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowspec.graph.graph import WorkflowGraph

__all__ = ["ExecutionStage", "build_execution_stages"]


@dataclass(frozen=True)
class ExecutionStage:
    """One group of steps that may run in parallel."""

    index: int
    steps: tuple[str, ...]


def build_execution_stages(graph: WorkflowGraph) -> list[ExecutionStage] | None:
    """The deterministic parallel stage schedule, or ``None`` if cyclic."""
    in_degree = {step: graph.in_degree(step) for step in graph.step_ids}
    ready = sorted(step for step in graph.step_ids if in_degree[step] == 0)
    stages: list[ExecutionStage] = []
    scheduled = 0

    while ready:
        stages.append(ExecutionStage(index=len(stages), steps=tuple(ready)))
        scheduled += len(ready)
        next_ready: set[str] = set()
        for node in ready:
            for successor in graph.successors(node):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    next_ready.add(successor)
        ready = sorted(next_ready)

    if scheduled != len(graph.step_ids):
        return None  # a cycle prevents scheduling (reported as E301/E104)
    return stages
