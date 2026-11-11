"""Expression type inference.

Infers the type of every expression in a workflow from workflow input
declarations, tool contracts, literal values, and previously resolved
references — deterministically, without any LLM involvement. Also
enforces the unknown-nominal-type policy (E203) on workflow input
declarations under strict typing.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Iterable

from flowspec.ast.expressions import (
    ExpressionNode,
    InputReferenceNode,
    LiteralNode,
    StepReferenceNode,
)
from flowspec.ast.workflow import WorkflowNode
from flowspec.config import CompilerConfig
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Diagnostic, Severity
from flowspec.exceptions import InternalError
from flowspec.typesystem.symbols import SymbolTable
from flowspec.typesystem.types import (
    BOOLEAN,
    FLOAT,
    INTEGER,
    NULL,
    STRING,
    NominalType,
    Type,
)

__all__ = ["TypeInference", "infer_expression_types"]


class TypeInference:
    """Expression types for one workflow, keyed by expression node."""

    def __init__(self, types: dict[ExpressionNode, Type]) -> None:
        self._types = types

    def of(self, expression: ExpressionNode) -> Type:
        """The inferred type of ``expression``.

        Raises :class:`InternalError` if the expression was never inferred
        — resolution failures skip inference for broken references, so
        callers must only query resolved expressions.
        """
        try:
            return self._types[expression]
        except KeyError:
            raise InternalError(f"no inferred type for expression {expression!r}") from None

    def get(self, expression: ExpressionNode) -> Type | None:
        """The inferred type of ``expression``, or ``None`` if unknown."""
        return self._types.get(expression)


def infer_expression_types(
    workflow: WorkflowNode,
    symbols: SymbolTable,
    config: CompilerConfig | None = None,
) -> tuple[TypeInference, list[Diagnostic]]:
    """Infer the type of every resolvable expression in ``workflow``."""
    config = config or CompilerConfig()
    types: dict[ExpressionNode, Type] = {}
    diagnostics: list[Diagnostic] = []

    _check_workflow_input_types(workflow, symbols, config, diagnostics)

    expressions: Iterable[ExpressionNode] = _all_expressions(workflow)
    for expression in expressions:
        inferred = _infer_expression(expression, symbols)
        if inferred is not None:
            types[expression] = inferred

    return TypeInference(types), diagnostics


def _all_expressions(workflow: WorkflowNode) -> list[ExpressionNode]:
    expressions: list[ExpressionNode] = []
    for step in workflow.steps:
        expressions.extend(step.inputs.values())
    for output in workflow.outputs.values():
        expressions.append(output.expression)
    return expressions


def _infer_expression(expression: ExpressionNode, symbols: SymbolTable) -> Type | None:
    if isinstance(expression, LiteralNode):
        return _literal_type(expression.value)
    if isinstance(expression, InputReferenceNode):
        symbol = symbols.resolve_input(expression.name)
        return symbol.type if symbol else None
    if isinstance(expression, StepReferenceNode):
        return symbols.step_output_type(expression.step, expression.output)
    return None  # pragma: no cover - future expression kinds


def _literal_type(value: object) -> Type:
    # bool must be tested before int: True is an int in Python.
    if isinstance(value, bool):
        return BOOLEAN
    if isinstance(value, int):
        return INTEGER
    if isinstance(value, float):
        return FLOAT
    if isinstance(value, str):
        return STRING
    if value is None:
        return NULL
    raise InternalError(f"unknown literal kind: {value!r}")  # pragma: no cover


def _check_workflow_input_types(
    workflow: WorkflowNode,
    symbols: SymbolTable,
    config: CompilerConfig,
    diagnostics: list[Diagnostic],
) -> None:
    """Unknown nominal types in input declarations are E203 under strict typing."""
    if not config.strict_types or config.allow_unknown_types:
        return
    known = symbols.known_nominal_types
    for input_symbol in symbols.inputs.values():
        if isinstance(input_symbol.type, NominalType) and input_symbol.type.name not in known:
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.TYPE_INFERENCE_FAILURE,
                    severity=Severity.ERROR,
                    message=(
                        f"workflow input {input_symbol.name!r} declares unknown "
                        f"nominal type {input_symbol.type.render()!r}: no tool "
                        f"contract declares it"
                    ),
                    workflow=workflow.name,
                    location=None,
                    expected="a type declared by a tool contract",
                    received=input_symbol.type.render(),
                )
            )
