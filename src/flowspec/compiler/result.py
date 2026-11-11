"""Compilation result objects.

``CompilationResult`` reports the outcome of a compilation: success with
the intermediate representation and execution stages, or failure with
aggregated, deduplicated, deterministically ordered structured
diagnostics. It never claims success for workflows that failed any
mandatory pass — an invalid workflow always has ``ir is None``.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowspec.compiler.ir import IntermediateRepresentation
from flowspec.diagnostics.formatter import format_diagnostics, format_summary
from flowspec.diagnostics.models import Diagnostic
from flowspec.graph.graph import WorkflowGraph
from flowspec.graph.scheduler import ExecutionStage

__all__ = ["CompilationResult"]


@dataclass(frozen=True)
class CompilationResult:
    """The outcome of one pipeline run.

    Attributes:
        workflow_name: the parsed workflow's name, or ``None`` when the
            source could not be parsed far enough to know it.
        diagnostics: every diagnostic from every pass, deduplicated and
            sorted deterministically.
        ir: the executable intermediate representation, or ``None``.
            Always ``None`` when any error-severity diagnostic exists;
            also ``None`` when IR generation is disabled by
            configuration.
        graph: the dependency graph when the workflow reached graph
            analysis, else ``None``.
        stages: the parallel execution stages when scheduling
            succeeded, else empty.
    """

    workflow_name: str | None
    diagnostics: tuple[Diagnostic, ...]
    ir: IntermediateRepresentation | None = None
    graph: WorkflowGraph | None = None
    stages: tuple[ExecutionStage, ...] = ()

    @property
    def success(self) -> bool:
        """Whether the workflow compiled without any error diagnostic."""
        return not self.has_errors

    @property
    def has_errors(self) -> bool:
        return any(diagnostic.is_error for diagnostic in self.diagnostics)

    @property
    def error_count(self) -> int:
        return sum(1 for diagnostic in self.diagnostics if diagnostic.is_error)

    @property
    def warning_count(self) -> int:
        return sum(1 for diagnostic in self.diagnostics if diagnostic.severity == "warning")

    @property
    def execution_order(self) -> tuple[str, ...]:
        """The topological execution order, or empty when unavailable."""
        if self.ir is not None:
            return self.ir.order
        return ()

    def summary(self) -> str:
        """A one-line diagnostic summary."""
        return format_summary(self.diagnostics)

    def formatted(self) -> str:
        """Every diagnostic rendered as plain text, one per line."""
        return format_diagnostics(self.diagnostics)

    def to_dict(self) -> dict[str, object]:
        """A JSON-friendly representation (without the full IR)."""
        return {
            "success": self.success,
            "workflow": self.workflow_name,
            "summary": self.summary(),
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
            "ir": self.ir.to_dict() if self.ir is not None else None,
        }
