"""Constraint validation engine (pipeline P10).

Compiles the declarative constraints implied by a resolved workflow —
``RequiredInput``, ``ReferenceExists``, ``DependencyExists``,
``NonNullRequired``, ``TypeCompatibility``, ``OutputExists``, and
``DependencyAcyclic`` — and evaluates them deterministically over the
compiled state. ``PermissionAvailable`` arrives with the permission
analyzer in v0.2.0.

The engine is an independent second net over the same invariants the
specialized passes check first (E101/E102/E103/E201/E202/E204/E301/E104).
It never executes anything and never consults anything outside the
compiled state: the same inputs always produce the same report.

Division of labor with the type checker: a nullable or null source
flowing into a non-``Optional`` target is a ``NonNullRequired``
violation, and ``TypeCompatibility`` deliberately skips that case —
each failure is reported through exactly one constraint kind, never
twice.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowspec.ast.expressions import (
    ExpressionNode,
    InputReferenceNode,
    StepReferenceNode,
    describe_expression,
)
from flowspec.ast.nodes import SourceLocation
from flowspec.ast.workflow import ToolCallNode, WorkflowNode
from flowspec.config import CompilerConfig
from flowspec.graph.cycle_detection import detect_cycles
from flowspec.graph.graph import WorkflowGraph
from flowspec.registry.tool_registry import ToolDefinition, ToolRegistry
from flowspec.typesystem.inference import TypeInference
from flowspec.typesystem.symbols import SymbolTable
from flowspec.typesystem.type_checker import TypeChecker
from flowspec.typesystem.types import Type, is_null, is_optional

__all__ = [
    "CONSTRAINT_KINDS",
    "Constraint",
    "ConstraintEngine",
    "ConstraintReport",
    "ConstraintViolation",
]

#: Every constraint kind the engine compiles in v0.1.0, in evaluation order.
CONSTRAINT_KINDS = (
    "RequiredInput",
    "ReferenceExists",
    "DependencyExists",
    "NonNullRequired",
    "TypeCompatibility",
    "OutputExists",
    "DependencyAcyclic",
)


@dataclass(frozen=True)
class Constraint:
    """One declarative constraint over the compiled workflow state."""

    kind: str
    subject: str
    requirement: str
    step: str | None = None
    location: SourceLocation | None = None


@dataclass(frozen=True)
class ConstraintViolation:
    """A constraint that does not hold, with the reason it failed."""

    constraint: Constraint
    reason: str
    expected: str | None = None
    received: str | None = None


@dataclass(frozen=True)
class ConstraintReport:
    """The outcome of evaluating every compiled constraint."""

    constraints: tuple[Constraint, ...]
    violations: tuple[ConstraintViolation, ...]

    @property
    def satisfied(self) -> bool:
        """Whether every compiled constraint holds."""
        return not self.violations


class ConstraintEngine:
    """Compiles and evaluates workflow constraints deterministically.

    The engine is constructed with a configuration (whose type-checking
    policy feeds ``TypeCompatibility``) and evaluates a fully resolved
    workflow state: AST, symbol table, registry, expression inference,
    and dependency graph.
    """

    def __init__(self, config: CompilerConfig | None = None) -> None:
        self.config = config or CompilerConfig()
        self.checker = TypeChecker(self.config)

    def evaluate(
        self,
        workflow: WorkflowNode,
        symbols: SymbolTable,
        registry: ToolRegistry,
        inference: TypeInference,
        graph: WorkflowGraph,
    ) -> ConstraintReport:
        """Compile and evaluate every constraint over the compiled state.

        Constraints are compiled in workflow declaration order (and by
        sorted argument name within a step), so the report is stable
        across runs. Evaluation never mutates any input.
        """
        constraints: list[Constraint] = []
        violations: list[ConstraintViolation] = []

        for step in workflow.steps:
            tool = registry.get(step.tool)
            if tool is None:
                continue  # unknown tool: no contract to constrain against (E401)

            self._required_input_constraints(step, tool, constraints, violations)
            for argument in sorted(step.inputs):
                self._argument_constraints(
                    step,
                    argument,
                    step.inputs[argument],
                    tool,
                    symbols,
                    inference,
                    graph,
                    constraints,
                    violations,
                )

        for output in workflow.outputs.values():
            self._output_constraint(
                output.name,
                output.expression,
                output.location,
                symbols,
                constraints,
                violations,
            )

        self._acyclic_constraint(graph, constraints, violations)

        return ConstraintReport(constraints=tuple(constraints), violations=tuple(violations))

    def _required_input_constraints(
        self,
        step: ToolCallNode,
        tool: ToolDefinition,
        constraints: list[Constraint],
        violations: list[ConstraintViolation],
    ) -> None:
        """``RequiredInput``: every required tool input is supplied."""
        for parameter in tool.inputs:
            if not parameter.required:
                continue
            constraint = Constraint(
                kind="RequiredInput",
                subject=f"step {step.id!r} input {parameter.name!r}",
                requirement=f"{parameter.name!r} must be supplied",
                step=step.id,
                location=step.location,
            )
            constraints.append(constraint)
            if parameter.name not in step.inputs:
                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        reason="the required input is not supplied",
                        expected=parameter.name,
                        received="not supplied",
                    )
                )

    def _argument_constraints(
        self,
        step: ToolCallNode,
        argument: str,
        expression: ExpressionNode,
        tool: ToolDefinition,
        symbols: SymbolTable,
        inference: TypeInference,
        graph: WorkflowGraph,
        constraints: list[Constraint],
        violations: list[ConstraintViolation],
    ) -> None:
        parameter = tool.input(argument)
        if parameter is None:
            return  # unknown argument: no contract to constrain against (E402)

        self._reference_constraints(step.id, argument, expression, symbols, constraints, violations)
        # DependencyExists only applies to references that resolve — an
        # unresolved reference is owned by ReferenceExists alone.
        if isinstance(expression, StepReferenceNode) and (
            _step_output_resolves(expression, symbols) is not None
        ):
            self._dependency_constraint(
                step.id, argument, expression, graph, constraints, violations
            )

        source_type = inference.get(expression)
        if source_type is None:
            return  # unresolved reference: already reported (E102/E103)

        target_type = parameter.effective_type
        if (is_null(source_type) or is_optional(source_type)) and not is_optional(target_type):
            # Exactly one constraint owns this case (see module docstring).
            constraint = Constraint(
                kind="NonNullRequired",
                subject=f"step {step.id!r} input {argument!r}",
                requirement=(
                    f"a nullable value must not satisfy the non-nullable parameter {argument!r}"
                ),
                step=step.id,
                location=expression.location,
            )
            constraints.append(constraint)
            violations.append(
                ConstraintViolation(
                    constraint=constraint,
                    reason=(
                        f"{source_type.render()} is nullable but {argument!r} does not accept null"
                    ),
                    expected=target_type.render(),
                    received=source_type.render(),
                )
            )
            return

        constraint = Constraint(
            kind="TypeCompatibility",
            subject=f"step {step.id!r} input {argument!r}",
            requirement=(
                f"a value of type {source_type.render()} must be assignable "
                f"to {target_type.render()}"
            ),
            step=step.id,
            location=expression.location,
        )
        constraints.append(constraint)
        result = self.checker.check_assignment(source_type, target_type)
        if not result.compatible:
            violations.append(
                ConstraintViolation(
                    constraint=constraint,
                    reason=result.reason or "the types are not compatible",
                    expected=target_type.render(),
                    received=source_type.render(),
                )
            )

    def _reference_constraints(
        self,
        step_id: str,
        argument: str,
        expression: ExpressionNode,
        symbols: SymbolTable,
        constraints: list[Constraint],
        violations: list[ConstraintViolation],
    ) -> None:
        """``ReferenceExists``: every reference resolves to a declared symbol."""
        if isinstance(expression, InputReferenceNode):
            constraint = Constraint(
                kind="ReferenceExists",
                subject=f"reference $input.{expression.name}",
                requirement=f"workflow input {expression.name!r} must be declared",
                step=step_id,
                location=expression.location,
            )
            constraints.append(constraint)
            if symbols.resolve_input(expression.name) is None:
                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        reason=f"workflow input {expression.name!r} is not declared",
                        expected="a declared workflow input",
                        received=f"$input.{expression.name}",
                    )
                )
            return

        if isinstance(expression, StepReferenceNode):
            constraint = Constraint(
                kind="ReferenceExists",
                subject=f"reference ${expression.step}.{expression.output}",
                requirement=(f"step {expression.step!r} must declare output {expression.output!r}"),
                step=step_id,
                location=expression.location,
            )
            constraints.append(constraint)
            if _step_output_resolves(expression, symbols) is None:
                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        reason=(
                            f"step {expression.step!r} does not declare output "
                            f"{expression.output!r}"
                        ),
                        expected="a declared step output",
                        received=f"${expression.step}.{expression.output}",
                    )
                )

    def _dependency_constraint(
        self,
        step_id: str,
        argument: str,
        expression: ExpressionNode,
        graph: WorkflowGraph,
        constraints: list[Constraint],
        violations: list[ConstraintViolation],
    ) -> None:
        """``DependencyExists``: every step reference is a real graph edge."""
        if not isinstance(expression, StepReferenceNode):
            return
        constraint = Constraint(
            kind="DependencyExists",
            subject=f"dependency {expression.step} -> {step_id}",
            requirement=(
                f"step {step_id!r} must depend on {expression.step!r} for input {argument!r}"
            ),
            step=step_id,
            location=expression.location,
        )
        constraints.append(constraint)
        if not graph.has_edge(expression.step, step_id):
            violations.append(
                ConstraintViolation(
                    constraint=constraint,
                    reason=(
                        f"no dependency edge {expression.step} -> {step_id} "
                        f"exists in the workflow graph"
                    ),
                    expected=f"{expression.step} -> {step_id}",
                    received="no edge",
                )
            )

    def _output_constraint(
        self,
        name: str,
        expression: ExpressionNode,
        location: SourceLocation | None,
        symbols: SymbolTable,
        constraints: list[Constraint],
        violations: list[ConstraintViolation],
    ) -> None:
        """``OutputExists``: workflow outputs bind to resolvable expressions."""
        source = describe_expression(expression)
        constraint = Constraint(
            kind="OutputExists",
            subject=f"workflow output {name!r}",
            requirement=f"{source} must resolve to a declared symbol",
            location=location,
        )
        constraints.append(constraint)
        if not _expression_resolves(expression, symbols):
            violations.append(
                ConstraintViolation(
                    constraint=constraint,
                    reason=f"{source} does not resolve to a declared symbol",
                    expected="a declared input or step output",
                    received=source,
                )
            )

    def _acyclic_constraint(
        self,
        graph: WorkflowGraph,
        constraints: list[Constraint],
        violations: list[ConstraintViolation],
    ) -> None:
        """``DependencyAcyclic``: the dependency graph has no cycles."""
        constraint = Constraint(
            kind="DependencyAcyclic",
            subject="the workflow dependency graph",
            requirement="the dependency graph must be acyclic",
        )
        constraints.append(constraint)
        cycles = detect_cycles(graph)
        if cycles:
            violations.append(
                ConstraintViolation(
                    constraint=constraint,
                    reason=(
                        "the dependency graph contains cycles: "
                        + ", ".join(cycle.path for cycle in cycles)
                    ),
                    expected="an acyclic dependency graph",
                    received=f"{len(cycles)} cycle(s)",
                )
            )


def _expression_resolves(expression: ExpressionNode, symbols: SymbolTable) -> bool:
    if isinstance(expression, InputReferenceNode):
        return symbols.resolve_input(expression.name) is not None
    if isinstance(expression, StepReferenceNode):
        return _step_output_resolves(expression, symbols) is not None
    return True  # literals always resolve


def _step_output_resolves(expression: StepReferenceNode, symbols: SymbolTable) -> Type | None:
    """The output's effective type when the reference resolves, else ``None``."""
    step_symbol = symbols.resolve_step(expression.step)
    if step_symbol is None or not step_symbol.contract_known:
        return None
    parameter = step_symbol.outputs.get(expression.output)
    if parameter is None:
        return None
    return parameter.effective_type
