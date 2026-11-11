"""The FlowSpec tool registry.

Tools declare explicit input and output contracts with parsed types,
required/nullable flags, side effects, permissions, and confirmation
requirements. The registry tracks known tools and the universe of nominal
type names their contracts declare — the basis for unknown-type policy
(E203) on workflow input declarations.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from flowspec.exceptions import DuplicateToolError
from flowspec.typesystem.types import GenericType, NominalType, Type, is_optional

__all__ = ["ParameterSpec", "ToolDefinition", "ToolRegistry"]


@dataclass(frozen=True)
class ParameterSpec:
    """One declared input or output of a tool."""

    name: str
    type: Type
    required: bool = True
    nullable: bool = False

    @property
    def effective_type(self) -> Type:
        """The parameter's type with nullability made explicit.

        A ``nullable`` parameter accepts null, so its effective type for
        compatibility checks is ``Optional[T]`` — the single rule every
        consumer (semantic analysis, constraints, inference) shares.
        """
        if self.nullable and not is_optional(self.type):
            return GenericType("Optional", (self.type,))
        return self.type


@dataclass(frozen=True)
class ToolDefinition:
    """A tool's full declared contract."""

    name: str
    description: str | None = None
    inputs: tuple[ParameterSpec, ...] = ()
    outputs: tuple[ParameterSpec, ...] = ()
    effects: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    requires_confirmation: bool = False

    def input(self, name: str) -> ParameterSpec | None:
        """The declared input with ``name``, if any."""
        return self._find(self.inputs, name)

    def output(self, name: str) -> ParameterSpec | None:
        """The declared output with ``name``, if any."""
        return self._find(self.outputs, name)

    @property
    def input_names(self) -> tuple[str, ...]:
        return tuple(parameter.name for parameter in self.inputs)

    @property
    def output_names(self) -> tuple[str, ...]:
        return tuple(parameter.name for parameter in self.outputs)

    @staticmethod
    def _find(parameters: tuple[ParameterSpec, ...], name: str) -> ParameterSpec | None:
        for parameter in parameters:
            if parameter.name == name:
                return parameter
        return None


class ToolRegistry:
    """The set of tools known to a compilation."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool; duplicate names are rejected."""
        if tool.name in self._tools:
            raise DuplicateToolError(f"tool {tool.name!r} is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """The tool with ``name``, if registered."""
        return self._tools.get(name)

    def require(self, name: str) -> ToolDefinition:
        """The tool with ``name``; raises :class:`KeyError` if missing."""
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"tool {name!r} is not registered")
        return tool

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def __iter__(self) -> Iterator[ToolDefinition]:
        for name in sorted(self._tools):
            yield self._tools[name]

    @property
    def tool_names(self) -> tuple[str, ...]:
        """Registered tool names in sorted order."""
        return tuple(sorted(self._tools))

    def known_nominal_types(self) -> set[str]:
        """Every nominal type name declared by any tool contract."""
        names: set[str] = set()
        for tool in self:
            for parameter in (*tool.inputs, *tool.outputs):
                _collect_nominal(parameter.type, names)
        return names


def _collect_nominal(type_: Type, names: set[str]) -> None:
    if isinstance(type_, NominalType):
        names.add(type_.name)
    elif hasattr(type_, "parameters"):
        for parameter in type_.parameters:  # type: ignore[attr-defined]
            _collect_nominal(parameter, names)
