"""Tool schema loading.

Loads tool definition files (``tools.yaml`` / ``tools.json``) into a
:class:`~flowspec.registry.tool_registry.ToolRegistry`, running structural
validation (E002) and parsing every type expression (E205). All failures
are reported as structured diagnostics — the loader never guesses and
never silently ignores a malformed contract.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from pathlib import Path

from flowspec.config import CompilerConfig
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Diagnostic, Severity
from flowspec.exceptions import TypeParseError
from flowspec.parser.document import Document
from flowspec.parser.loader import load_document
from flowspec.parser.validator import validate_tool_document
from flowspec.registry.tool_registry import ParameterSpec, ToolDefinition, ToolRegistry
from flowspec.typesystem.parser import parse_type
from flowspec.typesystem.types import Type

__all__ = ["load_tool_document", "load_tool_schema"]


def load_tool_schema(
    path: str | Path,
    config: CompilerConfig | None = None,
) -> tuple[ToolRegistry, list[Diagnostic]]:
    """Load a tool registry from a file path."""
    config = config or CompilerConfig()
    document = load_document(Path(path), config)
    return load_tool_document(document, config)


def load_tool_document(
    document: Document,
    config: CompilerConfig | None = None,
) -> tuple[ToolRegistry, list[Diagnostic]]:
    """Build a tool registry from a parsed tool document."""
    config = config or CompilerConfig()
    registry = ToolRegistry()

    structural = validate_tool_document(document)
    if any(diagnostic.is_error for diagnostic in structural):
        return registry, structural

    data = document.data
    tools = data.get("tools", {})
    diagnostics: list[Diagnostic] = []

    for tool_name in sorted(tools):
        tool = tools[tool_name]
        inputs, input_errors = _parse_parameters(
            tool_name, "input", tool.get("inputs", {}) or {}, document
        )
        outputs, output_errors = _parse_parameters(
            tool_name, "output", tool.get("outputs", {}) or {}, document
        )
        diagnostics.extend(input_errors)
        diagnostics.extend(output_errors)

        registry.register(
            ToolDefinition(
                name=tool_name,
                description=tool.get("description"),
                inputs=tuple(inputs),
                outputs=tuple(outputs),
                effects=tuple(tool.get("effects", []) or []),
                permissions=tuple(tool.get("permissions", []) or []),
                requires_confirmation=bool(tool.get("requires_confirmation", False)),
            )
        )

    return registry, diagnostics


def _parse_parameters(
    tool_name: str,
    kind: str,
    parameters: dict,
    document: Document,
) -> tuple[list[ParameterSpec], list[Diagnostic]]:
    specs: list[ParameterSpec] = []
    diagnostics: list[Diagnostic] = []
    for parameter_name in sorted(parameters):
        spec = parameters[parameter_name]
        type_name = spec.get("type")
        try:
            type_ = parse_type(type_name)
        except TypeParseError as exc:
            diagnostics.append(
                Diagnostic(
                    code=ErrorCodes.INVALID_GENERIC_TYPE,
                    severity=Severity.ERROR,
                    message=f"tool {tool_name!r} {kind} {parameter_name!r}: {exc.message}",
                    location=document.locate(spec),
                    expected="a valid type expression",
                    received=str(type_name),
                )
            )
            continue
        specs.append(
            ParameterSpec(
                name=parameter_name,
                type=type_,
                required=bool(spec.get("required", True)),
                nullable=bool(spec.get("nullable", False)),
            )
        )
    return specs, diagnostics


def describe_type(type_: Type) -> str:
    """Render a type for diagnostics (kept for API symmetry)."""
    return type_.render()
