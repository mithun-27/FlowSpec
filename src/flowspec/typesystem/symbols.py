"""Symbol table for FlowSpec name resolution.

Tracks workflow inputs, steps with their tool contracts, workflow
outputs, and the universe of known nominal type names. Used to resolve
every expression; declaration order in the source does not matter —
forward references are permitted while the dependency graph stays valid.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from flowspec.registry.tool_registry import ParameterSpec, ToolDefinition
from flowspec.typesystem.types import GenericType, Type

__all__ = ["InputSymbol", "OutputSymbol", "StepSymbol", "SymbolTable"]


@dataclass(frozen=True)
class InputSymbol:
    """A declared workflow input."""

    name: str
    type: Type
    required: bool


@dataclass(frozen=True)
class StepSymbol:
    """A declared workflow step and its tool's output contract.

    ``contract_known`` is ``False`` when the step's tool is not registered:
    the step exists for reference purposes, but its outputs cannot be
    validated — the unknown tool is itself already reported (E401).
    """

    id: str
    tool: str
    outputs: dict[str, ParameterSpec]
    contract_known: bool = True


@dataclass(frozen=True)
class OutputSymbol:
    """A declared workflow output binding."""

    name: str
    type: Type


@dataclass
class SymbolTable:
    """Every name a workflow may refer to."""

    inputs: dict[str, InputSymbol] = field(default_factory=dict)
    steps: dict[str, StepSymbol] = field(default_factory=dict)
    outputs: dict[str, OutputSymbol] = field(default_factory=dict)
    known_nominal_types: set[str] = field(default_factory=set)

    def declare_input(self, symbol: InputSymbol) -> None:
        self.inputs[symbol.name] = symbol

    def declare_step(self, symbol: StepSymbol) -> None:
        self.steps[symbol.id] = symbol

    def declare_output(self, symbol: OutputSymbol) -> None:
        self.outputs[symbol.name] = symbol

    def resolve_input(self, name: str) -> InputSymbol | None:
        return self.inputs.get(name)

    def resolve_step(self, step_id: str) -> StepSymbol | None:
        return self.steps.get(step_id)

    def step_output(self, step_id: str, output: str) -> ParameterSpec | None:
        """A step's declared output parameter, if the step and output exist."""
        step = self.steps.get(step_id)
        if step is None:
            return None
        return step.outputs.get(output)

    def step_output_type(self, step_id: str, output: str) -> Type | None:
        """The effective type of a step output (``Optional[T]`` if nullable)."""
        parameter = self.step_output(step_id, output)
        if parameter is None:
            return None
        if parameter.nullable and not _is_optional(parameter.type):
            return GenericType(base="Optional", parameters=(parameter.type,))
        return parameter.type

    @staticmethod
    def from_registry_tool(tool: ToolDefinition) -> dict[str, ParameterSpec]:
        """The output contract of a registered tool, keyed by output name."""
        return {parameter.name: parameter for parameter in tool.outputs}


def _is_optional(type_: Type) -> bool:
    return isinstance(type_, GenericType) and type_.base == "Optional"
