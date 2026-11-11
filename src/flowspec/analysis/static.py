"""Static analysis orchestration (pipeline P10).

Runs the declarative analyzers over a resolved, fully analyzed workflow
and aggregates their structured diagnostics. In the v0.1.0 foundation
this is the constraint re-verification pass: the
:class:`~flowspec.analysis.constraints.ConstraintEngine` re-checks every
invariant — required inputs, reference validity, type compatibility,
optional values, dependencies, acyclicity, and outputs — over the
compiled state, and violations are reported as E601 constraint
diagnostics.

The engine is deliberately a second, independent net: the specialized
passes (name resolution, semantic analysis, cycle detection) already
report these problems with their precise codes (E101/E102/E103/E201/
E202/E204/E301/E104). A constraint violation therefore means a
mandatory invariant did not survive compilation — it is never duplicate
noise for workflow-authoring mistakes. The pipeline runs this pass only
after every earlier pass is clean.

Effect, permission, reachability, and dataflow analyzers arrive in
v0.2.0 and will plug into this orchestrator.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from flowspec.analysis.constraints import ConstraintEngine, ConstraintViolation
from flowspec.ast.workflow import WorkflowNode
from flowspec.config import CompilerConfig
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Diagnostic, Severity
from flowspec.graph.graph import WorkflowGraph
from flowspec.registry.tool_registry import ToolRegistry
from flowspec.typesystem.inference import TypeInference
from flowspec.typesystem.symbols import SymbolTable

__all__ = ["StaticAnalyzer"]


class StaticAnalyzer:
    """Aggregates static analysis diagnostics over a resolved workflow."""

    def __init__(self, config: CompilerConfig | None = None) -> None:
        self.config = config or CompilerConfig()

    def analyze(
        self,
        workflow: WorkflowNode,
        symbols: SymbolTable,
        registry: ToolRegistry,
        inference: TypeInference,
        graph: WorkflowGraph,
    ) -> list[Diagnostic]:
        """Run every static analyzer over the compiled workflow state."""
        engine = ConstraintEngine(self.config)
        report = engine.evaluate(workflow, symbols, registry, inference, graph)
        return [self._to_diagnostic(workflow.name, violation) for violation in report.violations]

    @staticmethod
    def _to_diagnostic(workflow_name: str, violation: ConstraintViolation) -> Diagnostic:
        """A constraint violation as an E601 diagnostic."""
        constraint = violation.constraint
        return Diagnostic(
            code=ErrorCodes.CONSTRAINT_VIOLATION,
            severity=Severity.ERROR,
            message=(
                f"{constraint.kind} constraint violated for {constraint.subject}: "
                f"{violation.reason}"
            ),
            workflow=workflow_name,
            step=constraint.step,
            location=constraint.location,
            expected=violation.expected,
            received=violation.received,
            suggestions=(f"{constraint.kind}: {constraint.requirement}",),
        )
