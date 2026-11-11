"""Dependency extraction from workflows.

Extracts dependency edges wherever one step consumes an output of another
step, producing typed :class:`DependencyEdge` records for graph
construction. Only *resolved* references become edges — a reference whose
step or output is unknown (already reported as E102/E103 by name
resolution) never invents a graph edge.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowspec.ast.expressions import StepReferenceNode
from flowspec.ast.nodes import SourceLocation
from flowspec.ast.workflow import WorkflowNode
from flowspec.typesystem.symbols import SymbolTable

__all__ = ["DependencyEdge", "extract_dependencies"]


@dataclass(frozen=True)
class DependencyEdge:
    """One data dependency: ``from_step``.``output`` feeds ``to_step``.``argument``."""

    from_step: str
    to_step: str
    output: str
    argument: str
    location: SourceLocation | None = None

    @property
    def describe(self) -> str:
        """Human-readable form, e.g. ``customer.customer_id -> invoice.customer_id``."""
        return f"{self.from_step}.{self.output} -> {self.to_step}.{self.argument}"


def extract_dependencies(
    workflow: WorkflowNode,
    symbols: SymbolTable,
) -> list[DependencyEdge]:
    """Collect every resolvable step-to-step data dependency, in source order."""
    edges: list[DependencyEdge] = []
    for step in workflow.steps:
        for argument, expression in step.inputs.items():
            if not isinstance(expression, StepReferenceNode):
                continue
            step_symbol = symbols.resolve_step(expression.step)
            if step_symbol is None or not step_symbol.contract_known:
                continue
            if step_symbol.outputs.get(expression.output) is None:
                continue
            edges.append(
                DependencyEdge(
                    from_step=expression.step,
                    to_step=step.id,
                    output=expression.output,
                    argument=argument,
                    location=expression.location,
                )
            )
    return edges
