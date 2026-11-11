"""Semantic analysis of workflow declarations (pipeline P5/P6).

Validates each step against its tool contract after name resolution:
required tool inputs supplied (E101), no unknown arguments (E402), and
supplied values type-compatible with the contract (E201/E202/E204 via the
central :class:`~flowspec.typesystem.type_checker.TypeChecker`). Workflow
output bindings are validated for resolution by name resolution; their
types carry into the compiled result.

Steps whose tool is unregistered are skipped here — the unknown tool is
already reported (E401) and there is no contract to check against.
Expressions whose references did not resolve are skipped — they are
already reported (E102/E103).

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from flowspec.ast.workflow import ToolCallNode, WorkflowNode
from flowspec.config import CompilerConfig
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Diagnostic, Severity
from flowspec.registry.tool_registry import ParameterSpec, ToolDefinition, ToolRegistry
from flowspec.typesystem.inference import TypeInference, infer_expression_types
from flowspec.typesystem.symbols import SymbolTable
from flowspec.typesystem.type_checker import TypeChecker
from flowspec.typesystem.types import GenericType, Type, is_optional

__all__ = ["SemanticAnalyzer"]


class SemanticAnalyzer:
    """Analyzes a resolved workflow against its tool contracts."""

    def __init__(self, config: CompilerConfig | None = None) -> None:
        self.config = config or CompilerConfig()
        self.checker = TypeChecker(self.config)

    def analyze(
        self,
        workflow: WorkflowNode,
        symbols: SymbolTable,
        registry: ToolRegistry,
    ) -> tuple[TypeInference, list[Diagnostic]]:
        """Run full semantic analysis over ``workflow``.

        Returns the expression type inference (reused by later passes)
        and every diagnostic found.
        """
        inference, diagnostics = infer_expression_types(workflow, symbols, self.config)
        for step in workflow.steps:
            tool = registry.get(step.tool)
            if tool is None:
                continue  # unknown tool already reported (E401)
            self._check_required_inputs(workflow, step, tool, diagnostics)
            self._check_arguments(workflow, step, tool, inference, diagnostics)
        return inference, diagnostics

    def _check_required_inputs(
        self,
        workflow: WorkflowNode,
        step: ToolCallNode,
        tool: ToolDefinition,
        diagnostics: list[Diagnostic],
    ) -> None:
        for parameter in tool.inputs:
            if parameter.name in step.inputs:
                continue
            if parameter.required:
                diagnostics.append(
                    Diagnostic(
                        code=ErrorCodes.MISSING_DEPENDENCY,
                        severity=Severity.ERROR,
                        message=(
                            f"step {step.id!r} is missing required tool input {parameter.name!r}"
                        ),
                        workflow=workflow.name,
                        step=step.id,
                        location=step.location,
                        expected=parameter.name,
                        received="not supplied",
                        suggestions=(f"supply {parameter.name!r} in step {step.id!r}",),
                    )
                )

    def _check_arguments(
        self,
        workflow: WorkflowNode,
        step: ToolCallNode,
        tool: ToolDefinition,
        inference: TypeInference,
        diagnostics: list[Diagnostic],
    ) -> None:
        for argument, expression in step.inputs.items():
            parameter = tool.input(argument)
            if parameter is None:
                diagnostics.append(
                    Diagnostic(
                        code=ErrorCodes.INVALID_TOOL_ARGUMENT,
                        severity=Severity.ERROR,
                        message=(
                            f"step {step.id!r} passes unknown argument "
                            f"{argument!r} to tool {tool.name!r}"
                        ),
                        workflow=workflow.name,
                        step=step.id,
                        location=expression.location,
                        expected=_expected_arguments(tool),
                        received=argument,
                    )
                )
                continue

            source_type = inference.get(expression)
            if source_type is None:
                continue  # unresolved reference already reported (E102/E103)

            target_type = _effective_target(parameter)
            result = self.checker.check_assignment(source_type, target_type)
            if not result.compatible:
                diagnostics.append(
                    Diagnostic(
                        code=result.failure_code,
                        severity=Severity.ERROR,
                        message=(f"step {step.id!r} argument {argument!r}: {result.reason}"),
                        workflow=workflow.name,
                        step=step.id,
                        location=expression.location,
                        expected=target_type.render(),
                        received=source_type.render(),
                    )
                )


def _expected_arguments(tool: ToolDefinition) -> str:
    if not tool.input_names:
        return "no inputs"
    return f"one of: {', '.join(tool.input_names)}"


def _effective_target(parameter: ParameterSpec) -> Type:
    """Nullable parameters accept null: their effective type is Optional[T]."""
    if parameter.nullable and not is_optional(parameter.type):
        return GenericType("Optional", (parameter.type,))
    return parameter.type
