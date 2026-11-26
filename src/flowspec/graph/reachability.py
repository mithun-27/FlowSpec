"""Reachability and dead-step analysis (E303).

Finds steps that cannot contribute to any workflow output or required side
effect. A step is reachable when it is a root or when a root (directly or
transitively) consumes one of its outputs.

Roots are:

- steps referenced by ``workflow.outputs``;
- steps whose tool declares an effect other than a pure ``read`` — those
  side effects are required by the workflow even without an output edge.

Dead steps are reported as structured diagnostics, never removed
automatically. Workflows with no roots — no step-referencing outputs and
no required side effects — have no reachability requirement and are
skipped. Results are deterministic: root and unreachable-step order
follows the graph's declaration order.

Analysis is read-only: it returns unreachable step ids for E303 diagnostics
and leaves those steps in the compiled workflow.

Status: implemented for the v0.1.0 compiler foundation; see
``docs/PROGRESS.md``.
"""

from __future__ import annotations

from flowspec.ast.expressions import StepReferenceNode
from flowspec.ast.workflow import WorkflowNode
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Diagnostic, Severity
from flowspec.graph.graph import WorkflowGraph
from flowspec.registry.tool_registry import ToolRegistry

__all__ = ["analyze_reachability", "unreachable_steps"]

#: Effects that do not need to happen unless their value is consumed.
_PURE_READ_EFFECTS = frozenset({"read"})


def _root_steps(
    graph: WorkflowGraph,
    workflow: WorkflowNode,
    registry: ToolRegistry,
) -> tuple[str, ...]:
    """The steps whose results or side effects the workflow requires."""
    roots: set[str] = set()
    for output in workflow.outputs.values():
        expression = output.expression
        if isinstance(expression, StepReferenceNode) and expression.step in graph:
            roots.add(expression.step)

    for step in workflow.steps:
        tool = registry.get(step.tool)
        if tool is None:  # unknown tools are E401, reported by name resolution
            continue
        if any(effect not in _PURE_READ_EFFECTS for effect in tool.effects):
            roots.add(step.id)

    if not roots:
        # Nothing declares a step result or side effect as required, so no
        # step can be called dead relative to that requirement.
        return graph.step_ids

    return tuple(step for step in graph.step_ids if step in roots)


def unreachable_steps(
    graph: WorkflowGraph,
    workflow: WorkflowNode,
    registry: ToolRegistry,
) -> tuple[str, ...]:
    """Step ids that cannot reach any root, in declaration order."""
    reachable: set[str] = set()
    stack = list(_root_steps(graph, workflow, registry))
    while stack:
        step = stack.pop()
        if step in reachable:
            continue
        reachable.add(step)
        stack.extend(graph.predecessors(step))

    return tuple(step for step in graph.step_ids if step not in reachable)


def analyze_reachability(
    graph: WorkflowGraph,
    workflow: WorkflowNode,
    registry: ToolRegistry,
) -> tuple[Diagnostic, ...]:
    """Diagnose dead steps with E303; never remove or rewrite them."""
    diagnostics: list[Diagnostic] = []
    for step_id in unreachable_steps(graph, workflow, registry):
        step = workflow.find_step(step_id)
        diagnostics.append(
            Diagnostic(
                code=ErrorCodes.UNREACHABLE_STEP,
                severity=Severity.ERROR,
                message=(
                    f"step '{step_id}' is unreachable: it cannot contribute to "
                    "any workflow output or required side effect"
                ),
                workflow=workflow.name,
                step=step_id,
                location=step.location if step is not None else None,
                suggestions=(
                    "reference its output in a later step or in workflow.outputs",
                    "remove the step if it is not needed",
                ),
            )
        )
    return tuple(diagnostics)
