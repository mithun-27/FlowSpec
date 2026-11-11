"""Compilation pass orchestration (specification §4.1).

Runs the ordered pipeline passes over a workflow and its tool schema,
aggregating diagnostics across passes into one
:class:`~flowspec.compiler.result.CompilationResult`:

- **P0-P2** load and parse both documents, validate their structure,
  and build the workflow AST. Structural failures end the run early
  with the diagnostics found so far.
- **P3-P6** resolve names against the registry, then run semantic
  analysis (which performs type inference and type checking through the
  central checker).
- **P7-P8** build the dependency graph, diagnose cycles (when cycle
  detection is enabled), and compute the deterministic topological order
  and parallel execution stages.
- **P10** run the constraint engine — only when every earlier pass was
  clean, so constraint violations are never duplicate noise for
  problems already reported with precise codes.
- **P12** emit the versioned IR — only for workflows with zero error
  diagnostics and a valid execution order. Invalid workflows never
  produce executable IR.

Compilation is deterministic — the same sources and configuration
always produce the same diagnostics, order, stages, and IR — and never
executes a tool. Missing or unreadable source files raise
:class:`~flowspec.exceptions.ConfigurationError` (CLI exit code 2);
everything about the *workflow itself* is reported as diagnostics.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from pathlib import Path

from flowspec.analysis.static import StaticAnalyzer
from flowspec.compiler.ir import IntermediateRepresentation
from flowspec.compiler.result import CompilationResult
from flowspec.config import CompilerConfig
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Diagnostic, DiagnosticCollection, Severity
from flowspec.exceptions import SourceError
from flowspec.graph.cycle_detection import cycle_diagnostics
from flowspec.graph.graph import WorkflowGraph
from flowspec.graph.scheduler import ExecutionStage, build_execution_stages
from flowspec.graph.topological_sort import topological_sort
from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.document import Document
from flowspec.parser.loader import load_document
from flowspec.parser.validator import validate_workflow_document
from flowspec.registry.schema_loader import load_tool_document
from flowspec.semantic.name_resolution import resolve_workflow
from flowspec.semantic.semantic_analyzer import SemanticAnalyzer

__all__ = ["PIPELINE_PASSES", "CompilationPipeline"]

#: The documented compilation passes (see docs/compiler_pipeline.md),
#: with their v0.1.0 implementation status.
PIPELINE_PASSES: tuple[tuple[str, str, str], ...] = (
    ("P0", "Source loading", "implemented"),
    ("P1", "Syntax parsing", "implemented"),
    ("P2", "AST construction", "implemented"),
    ("P3", "Name resolution", "implemented"),
    ("P4", "Semantic analysis", "implemented"),
    ("P5", "Type inference", "implemented"),
    ("P6", "Type checking", "implemented"),
    ("P7", "Dependency analysis", "implemented"),
    ("P8", "Graph analysis", "implemented"),
    ("P9", "Dataflow analysis", "planned for v0.2.0"),
    ("P10", "Constraint analysis", "implemented"),
    ("P11", "Effect analysis", "planned for v0.2.0"),
    ("P12", "IR generation", "implemented"),
)

#: Sibling tool-schema files looked up when no tools path is given,
#: in preference order.
_DEFAULT_TOOL_FILES = ("tools.yaml", "tools.json")


class CompilationPipeline:
    """Runs the full compilation pipeline over a workflow project."""

    def __init__(self, config: CompilerConfig | None = None) -> None:
        self.config = config or CompilerConfig()

    def run(
        self,
        workflow_path: str | Path,
        tools_path: str | Path | None = None,
    ) -> CompilationResult:
        """Compile ``workflow_path`` (with ``tools_path``, or the sibling
        ``tools.yaml``/``tools.json``) and return the result."""
        workflow_file = Path(workflow_path)
        tools_file = self._resolve_tools_path(workflow_file, tools_path)
        sink = DiagnosticCollection()
        workflow_name: str | None = None

        def result(
            ir: IntermediateRepresentation | None = None,
            graph: WorkflowGraph | None = None,
            stages: tuple[ExecutionStage, ...] = (),
        ) -> CompilationResult:
            return CompilationResult(
                workflow_name=workflow_name,
                diagnostics=tuple(sink.sorted()),
                ir=ir,
                graph=graph,
                stages=stages,
            )

        # P0/P1: load and parse the workflow document.
        workflow_document = self._load(workflow_file, sink)
        if workflow_document is None:
            return result()

        structure = validate_workflow_document(workflow_document)
        sink.extend(structure)
        if any(diagnostic.is_error for diagnostic in structure):
            return result()  # no AST possible; report what was found

        # P2: AST construction.
        try:
            workflow = build_workflow_ast(workflow_document)
        except SourceError as exc:
            sink.add(self._source_diagnostic(exc))
            return result()
        workflow_name = workflow.name

        # P0/P1: load the tool schema; structural failures (E002) end the
        # run here — an empty registry would turn every tool into E401 noise.
        tools_document = self._load(tools_file, sink)
        if tools_document is None:
            return result()
        registry, tool_diagnostics = load_tool_document(tools_document, self.config)
        sink.extend(tool_diagnostics)
        if any(diagnostic.code == "E002" for diagnostic in tool_diagnostics):
            return result()
        # E205 type-expression failures keep the (otherwise valid) tools
        # registered; the run continues and the errors block IR at the end.

        # P3: name resolution.
        resolution = resolve_workflow(workflow, registry, self.config)
        sink.extend(resolution.diagnostics)

        # P4/P5/P6: semantic analysis (declaration checks, inference, and
        # type checking against the contracts).
        analyzer = SemanticAnalyzer(self.config)
        inference, semantic = analyzer.analyze(workflow, resolution.symbols, registry)
        sink.extend(semantic)

        # P7/P8: dependency graph, cycles, ordering, and stages.
        graph = WorkflowGraph.from_workflow(workflow, resolution.symbols)
        if self.config.detect_cycles:
            sink.extend(cycle_diagnostics(graph, workflow.name))
        order = topological_sort(graph)
        stages = build_execution_stages(graph)
        if order is None and not self._cycles_already_reported(sink):
            # Cycle detection is disabled but no valid order exists; the
            # workflow cannot be scheduled, so it cannot compile.
            sink.add(
                Diagnostic(
                    code=ErrorCodes.INVALID_EXECUTION_ORDER,
                    severity=Severity.ERROR,
                    message=(
                        "no valid execution order exists: the workflow "
                        "dependency graph contains a cycle"
                    ),
                    workflow=workflow.name,
                    suggestions=(
                        "remove the circular dependency",
                        "enable cycle detection (detect_cycles) to see the cycle path",
                    ),
                )
            )
        if stages is None:
            stages = []

        # P10: constraint analysis — the final gate, only over clean state.
        if not sink.has_errors:
            static_analyzer = StaticAnalyzer(self.config)
            sink.extend(
                static_analyzer.analyze(workflow, resolution.symbols, registry, inference, graph)
            )

        # P12: IR generation — valid workflows only.
        ir = None
        if not sink.has_errors and self.config.generate_ir and order is not None:
            ir = IntermediateRepresentation.build(
                workflow,
                registry,
                inference,
                graph,
                tuple(order),
                stages,
            )

        return result(ir=ir, graph=graph, stages=tuple(stages))

    # --- Helpers ------------------------------------------------------

    def _load(self, path: Path, sink: DiagnosticCollection) -> Document | None:
        """Load and parse one source document (P0/P1).

        Returns ``None`` (after recording an E001/E002 diagnostic) when
        the document cannot be parsed. Unreadable or missing files raise
        :class:`~flowspec.exceptions.ConfigurationError` — that is a
        project problem, not a workflow problem.
        """
        try:
            return load_document(path, self.config)
        except SourceError as exc:
            sink.add(self._source_diagnostic(exc))
            return None

    @staticmethod
    def _resolve_tools_path(workflow_file: Path, tools_path: str | Path | None) -> Path:
        """The tools schema path: explicit, or the workflow's sibling file."""
        if tools_path is not None:
            return Path(tools_path)
        for candidate in _DEFAULT_TOOL_FILES:
            sibling = workflow_file.parent / candidate
            if sibling.is_file():
                return sibling
        # Fall back to tools.yaml: the load will raise an actionable
        # ConfigurationError naming the expected file.
        return workflow_file.parent / "tools.yaml"

    @staticmethod
    def _source_diagnostic(exc: SourceError) -> Diagnostic:
        """A source-parse failure as a diagnostic (E001/E002)."""
        return Diagnostic(
            code=exc.code,
            severity=Severity.ERROR,
            message=exc.message,
            location=exc.location,
        )

    @staticmethod
    def _cycles_already_reported(sink: DiagnosticCollection) -> bool:
        """Whether the sink already carries cycle diagnostics (E301/E104)."""
        return any(diagnostic.code in ("E301", "E104") for diagnostic in sink.diagnostics)
