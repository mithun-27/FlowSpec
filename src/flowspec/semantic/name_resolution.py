"""Name resolution for FlowSpec workflows (pipeline P4).

Resolves tool references against the registry and data references
(``$input.*`` and ``$step.*``) against the symbol table, reporting unknown
tools (E401), duplicate step ids (E304), unknown output references (E102),
unresolved variables (E103), and malformed input type declarations (E205).
Resolution is order-independent — forward references are allowed as long
as the dependency graph remains valid.

Cascade prevention: a step whose tool is not registered is declared with
``contract_known=False`` so references *to* that step are not re-reported as
unknown outputs; a workflow input with a malformed type is excluded from
reference checking for the same reason.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowspec.ast.expressions import (
    ExpressionNode,
    InputReferenceNode,
    StepReferenceNode,
)
from flowspec.ast.workflow import WorkflowNode
from flowspec.config import CompilerConfig
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Diagnostic, Severity
from flowspec.exceptions import TypeParseError
from flowspec.registry.tool_registry import ToolRegistry
from flowspec.typesystem.parser import parse_type
from flowspec.typesystem.symbols import (
    InputSymbol,
    StepSymbol,
    SymbolTable,
)
from flowspec.typesystem.types import Type

__all__ = ["NameResolution", "resolve_workflow"]


@dataclass(frozen=True)
class NameResolution:
    """The result of resolving a workflow's names."""

    symbols: SymbolTable
    diagnostics: tuple[Diagnostic, ...]


def resolve_workflow(
    workflow: WorkflowNode,
    registry: ToolRegistry,
    config: CompilerConfig | None = None,
) -> NameResolution:
    """Resolve every name in ``workflow`` against ``registry``.

    Produces the symbol table later passes consume plus all resolution
    diagnostics. Never raises for workflow problems — everything
    resolvable is resolved, everything uncertain is reported. ``config``
    is accepted for pipeline signature stability; resolution itself is
    configuration-independent in v0.1.0.
    """
    symbols = SymbolTable(known_nominal_types=registry.known_nominal_types())
    diagnostics: list[Diagnostic] = []

    broken_inputs = _declare_inputs(workflow, symbols, diagnostics)
    _declare_steps(workflow, registry, symbols, diagnostics)
    _resolve_references(workflow, symbols, broken_inputs, diagnostics)

    return NameResolution(symbols=symbols, diagnostics=tuple(diagnostics))


def _declare_inputs(
    workflow: WorkflowNode,
    symbols: SymbolTable,
    diagnostics: list[Diagnostic],
) -> set[str]:
    """Declare workflow inputs; return the names whose types failed to parse."""
    broken: set[str] = set()
    for input_node in workflow.inputs.values():
        try:
            type_: Type = parse_type(input_node.type_name)
        except TypeParseError as exc:
            broken.add(input_node.name)
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.INVALID_GENERIC_TYPE,
                    severity=Severity.ERROR,
                    message=(
                        f"workflow input {input_node.name!r} has a malformed "
                        f"type expression: {exc.message}"
                    ),
                    workflow=workflow.name,
                    location=input_node.location,
                    expected="a valid type expression",
                    received=input_node.type_name,
                )
            )
            continue
        symbols.declare_input(InputSymbol(input_node.name, type_, input_node.required))
    return broken


def _declare_steps(
    workflow: WorkflowNode,
    registry: ToolRegistry,
    symbols: SymbolTable,
    diagnostics: list[Diagnostic],
) -> None:
    seen: set[str] = set()
    for step in workflow.steps:
        if step.id in seen:
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.DUPLICATE_STEP_ID,
                    severity=Severity.ERROR,
                    message=f"duplicate step id {step.id!r}",
                    workflow=workflow.name,
                    step=step.id,
                    location=step.location,
                    suggestions=("step ids must be unique within a workflow",),
                )
            )
            continue
        seen.add(step.id)

        tool = registry.get(step.tool)
        if tool is None:
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.UNKNOWN_TOOL,
                    severity=Severity.ERROR,
                    message=f"step {step.id!r} uses unregistered tool {step.tool!r}",
                    workflow=workflow.name,
                    step=step.id,
                    location=step.location,
                    expected="a tool registered in the tool schema",
                    received=step.tool,
                    suggestions=(
                        f"register {step.tool!r} in the tool schema",
                        "check the tool name for typos",
                    ),
                )
            )
            symbols.declare_step(StepSymbol(step.id, step.tool, {}, contract_known=False))
            continue

        symbols.declare_step(StepSymbol(step.id, step.tool, SymbolTable.from_registry_tool(tool)))


def _resolve_references(
    workflow: WorkflowNode,
    symbols: SymbolTable,
    broken_inputs: set[str],
    diagnostics: list[Diagnostic],
) -> None:
    for step in workflow.steps:
        for argument, expression in step.inputs.items():
            context = f"step {step.id!r} argument {argument!r}"
            _check_expression(
                workflow, step.id, context, expression, symbols, broken_inputs, diagnostics
            )
    for output in workflow.outputs.values():
        context = f"workflow output {output.name!r}"
        _check_expression(
            workflow, None, context, output.expression, symbols, broken_inputs, diagnostics
        )


def _check_expression(
    workflow: WorkflowNode,
    step_id: str | None,
    context: str,
    expression: ExpressionNode,
    symbols: SymbolTable,
    broken_inputs: set[str],
    diagnostics: list[Diagnostic],
) -> None:
    if isinstance(expression, InputReferenceNode):
        symbol = symbols.resolve_input(expression.name)
        if symbol is None:
            if expression.name in broken_inputs:
                return  # the malformed declaration is already reported (E205)
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.UNRESOLVED_VARIABLE,
                    severity=Severity.ERROR,
                    message=f"{context} references unknown workflow input {expression.name!r}",
                    workflow=workflow.name,
                    step=step_id,
                    location=expression.location,
                    expected="a declared workflow input",
                    received=f"$input.{expression.name}",
                    suggestions=(f"declare {expression.name!r} in the workflow inputs",),
                )
            )
        return

    if isinstance(expression, StepReferenceNode):
        step_symbol = symbols.resolve_step(expression.step)
        if step_symbol is None:
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.UNRESOLVED_VARIABLE,
                    severity=Severity.ERROR,
                    message=f"{context} references unknown step {expression.step!r}",
                    workflow=workflow.name,
                    step=step_id,
                    location=expression.location,
                    expected="a declared workflow step",
                    received=f"${expression.step}.{expression.output}",
                    suggestions=(f"check the step id {expression.step!r}",),
                )
            )
            return
        if not step_symbol.contract_known:
            return  # the unknown tool is already reported (E401)
        parameter = step_symbol.outputs.get(expression.output)
        if parameter is None:
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.UNKNOWN_OUTPUT_REFERENCE,
                    severity=Severity.ERROR,
                    message=(
                        f"{context} references unknown output {expression.output!r} "
                        f"of step {expression.step!r} (tool {step_symbol.tool!r} "
                        f"declares no such output)"
                    ),
                    workflow=workflow.name,
                    step=step_id,
                    location=expression.location,
                    expected=_expected_outputs(step_symbol),
                    received=f"${expression.step}.{expression.output}",
                )
            )


def _expected_outputs(step_symbol: StepSymbol) -> str:
    if not step_symbol.outputs:
        return "no outputs"
    return f"one of: {', '.join(sorted(step_symbol.outputs))}"
