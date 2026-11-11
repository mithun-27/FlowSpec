"""Structural validation of parsed workflow and tool documents.

Validates that loaded YAML/JSON documents conform to the FlowSpec schema
shapes (specification §5) *before* AST construction, reporting all E002
structure diagnostics it can find — not just the first. Type expressions
and reference syntax are checked by later passes; this module only checks
shape.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from typing import Any

from flowspec.ast.nodes import SourceLocation
from flowspec.diagnostics.models import Diagnostic, Severity
from flowspec.parser.document import Document

__all__ = ["KNOWN_EFFECTS", "validate_tool_document", "validate_workflow_document"]

KNOWN_EFFECTS = (
    "read",
    "write",
    "external_write",
    "destructive",
    "financial",
    "network",
    "unknown",
)

SUPPORTED_VERSION = "1.0"


def _is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def _error(
    doc: Document,
    container: Any,
    message: str,
    *,
    workflow: str | None = None,
    step: str | None = None,
    expected: str | None = None,
    received: str | None = None,
) -> Diagnostic:
    location: SourceLocation | None = doc.locate(container)
    return Diagnostic(
        code="E002",
        severity=Severity.ERROR,
        message=message,
        workflow=workflow,
        step=step,
        location=location,
        expected=expected,
        received=received,
    )


def _check_version(doc: Document, data: Any, errors: list[Diagnostic]) -> None:
    if "version" not in data:
        errors.append(_error(doc, data, "document is missing the required 'version' key"))
        return
    version = data["version"]
    if not isinstance(version, str):
        errors.append(
            _error(
                doc,
                data,
                "'version' must be a string",
                expected="string",
                received=type(version).__name__,
            )
        )
    elif version != SUPPORTED_VERSION:
        errors.append(
            _error(
                doc,
                data,
                f"unsupported schema version {version!r}",
                expected=SUPPORTED_VERSION,
                received=version,
            )
        )


def validate_workflow_document(doc: Document) -> list[Diagnostic]:
    """Validate the structure of a parsed workflow document (E002)."""
    errors: list[Diagnostic] = []
    data = doc.data
    if not isinstance(data, dict):
        errors.append(
            _error(
                doc,
                data,
                "workflow document root must be a mapping",
                expected="mapping",
                received=type(data).__name__,
            )
        )
        return errors

    _check_version(doc, data, errors)

    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        errors.append(
            _error(
                doc,
                data,
                "document is missing the required 'workflow' mapping",
                expected="mapping",
                received=type(workflow).__name__,
            )
        )
        return errors

    _validate_workflow_section(doc, workflow, errors)
    return errors


def _validate_workflow_section(doc: Document, workflow: dict, errors: list[Diagnostic]) -> None:
    name = workflow.get("name")
    if not isinstance(name, str) or not name:
        errors.append(
            _error(
                doc,
                workflow,
                "workflow must declare a non-empty 'name' string",
                expected="string",
                received=type(name).__name__ if name is not None else "missing",
            )
        )

    description = workflow.get("description")
    if description is not None and not isinstance(description, str):
        errors.append(_error(doc, workflow, "workflow 'description' must be a string"))

    declared_inputs = workflow.get("inputs", {})
    if not isinstance(declared_inputs, dict):
        errors.append(
            _error(
                doc,
                workflow,
                "workflow 'inputs' must be a mapping",
                expected="mapping",
                received=type(declared_inputs).__name__,
            )
        )
    else:
        for input_name, spec in declared_inputs.items():
            if not isinstance(spec, dict):
                errors.append(
                    _error(
                        doc,
                        declared_inputs,
                        f"workflow input {input_name!r} must be a mapping",
                    )
                )
                continue
            _check_typed_spec(doc, declared_inputs, f"workflow input {input_name!r}", spec, errors)

    steps = workflow.get("steps")
    if not isinstance(steps, list):
        errors.append(
            _error(
                doc,
                workflow,
                "workflow must declare 'steps' as a list",
                expected="list",
                received=type(steps).__name__,
            )
        )
    else:
        for index, step in enumerate(steps):
            _validate_step(doc, steps, index, step, errors)

    outputs = workflow.get("outputs", {})
    if not isinstance(outputs, dict):
        errors.append(
            _error(
                doc,
                workflow,
                "workflow 'outputs' must be a mapping",
                expected="mapping",
                received=type(outputs).__name__,
            )
        )
    else:
        for output_name, expression in outputs.items():
            if not _is_scalar(expression):
                errors.append(
                    _error(
                        doc,
                        outputs,
                        f"workflow output {output_name!r} must be a scalar expression",
                        received=type(expression).__name__,
                    )
                )


def _validate_step(
    doc: Document, steps: list, index: int, step: Any, errors: list[Diagnostic]
) -> None:
    label = f"steps[{index}]"
    if not isinstance(step, dict):
        errors.append(
            _error(doc, steps, f"{label} must be a mapping", received=type(step).__name__)
        )
        return

    for key in ("id", "tool"):
        value = step.get(key)
        if not isinstance(value, str) or not value:
            errors.append(
                _error(
                    doc,
                    step,
                    f"{label} must declare a non-empty '{key}' string",
                    received=type(value).__name__ if value is not None else "missing",
                )
            )

    step_inputs = step.get("inputs", {})
    if not isinstance(step_inputs, dict):
        errors.append(
            _error(
                doc,
                step,
                f"{label} 'inputs' must be a mapping",
                expected="mapping",
                received=type(step_inputs).__name__,
            )
        )
    else:
        for argument, expression in step_inputs.items():
            if not _is_scalar(expression):
                errors.append(
                    _error(
                        doc,
                        step_inputs,
                        f"{label} argument {argument!r} must be a scalar expression",
                        received=type(expression).__name__,
                    )
                )


def _check_typed_spec(
    doc: Document,
    container: Any,
    label: str,
    spec: dict,
    errors: list[Diagnostic],
) -> None:
    type_name = spec.get("type")
    if not isinstance(type_name, str) or not type_name:
        errors.append(
            _error(
                doc,
                container,
                f"{label} must declare a non-empty 'type' string",
                received=type(type_name).__name__ if type_name is not None else "missing",
            )
        )
    for flag in ("required", "nullable"):
        value = spec.get(flag)
        if value is not None and not isinstance(value, bool):
            errors.append(
                _error(
                    doc,
                    container,
                    f"{label} flag '{flag}' must be a boolean",
                    expected="boolean",
                    received=type(value).__name__,
                )
            )


def validate_tool_document(doc: Document) -> list[Diagnostic]:
    """Validate the structure of a parsed tool registry document (E002)."""
    errors: list[Diagnostic] = []
    data = doc.data
    if not isinstance(data, dict):
        errors.append(
            _error(
                doc,
                data,
                "tool document root must be a mapping",
                expected="mapping",
                received=type(data).__name__,
            )
        )
        return errors

    _check_version(doc, data, errors)

    tools = data.get("tools")
    if not isinstance(tools, dict):
        errors.append(
            _error(
                doc,
                data,
                "tool document is missing the required 'tools' mapping",
                expected="mapping",
                received=type(tools).__name__,
            )
        )
        return errors

    for tool_name, tool in tools.items():
        _validate_tool(doc, tools, tool_name, tool, errors)

    return errors


def _validate_tool(
    doc: Document,
    tools: dict,
    tool_name: str,
    tool: Any,
    errors: list[Diagnostic],
) -> None:
    if not isinstance(tool, dict):
        errors.append(
            _error(
                doc,
                tools,
                f"tool {tool_name!r} must be a mapping",
                received=type(tool).__name__,
            )
        )
        return

    description = tool.get("description")
    if description is not None and not isinstance(description, str):
        errors.append(_error(doc, tool, f"tool {tool_name!r} 'description' must be a string"))

    for section in ("inputs", "outputs"):
        params = tool.get(section, {})
        if not isinstance(params, dict):
            errors.append(
                _error(
                    doc,
                    tool,
                    f"tool {tool_name!r} '{section}' must be a mapping",
                    expected="mapping",
                    received=type(params).__name__,
                )
            )
            continue
        for param_name, spec in params.items():
            if not isinstance(spec, dict):
                errors.append(
                    _error(
                        doc,
                        params,
                        f"tool {tool_name!r} {section[:-1]} {param_name!r} must be a mapping",
                    )
                )
                continue
            _check_typed_spec(
                doc, params, f"tool {tool_name!r} {section[:-1]} {param_name!r}", spec, errors
            )

    effects = tool.get("effects", [])
    if not isinstance(effects, list):
        errors.append(
            _error(
                doc,
                tool,
                f"tool {tool_name!r} 'effects' must be a list",
                expected="list",
                received=type(effects).__name__,
            )
        )
    else:
        for effect in effects:
            if not isinstance(effect, str):
                errors.append(
                    _error(
                        doc,
                        tool,
                        f"tool {tool_name!r} effect {effect!r} must be a string",
                    )
                )
            elif effect not in KNOWN_EFFECTS:
                errors.append(
                    _error(
                        doc,
                        tool,
                        f"tool {tool_name!r} declares unknown effect {effect!r}",
                        expected=f"one of {', '.join(KNOWN_EFFECTS)}",
                        received=effect,
                    )
                )

    permissions = tool.get("permissions", [])
    if not isinstance(permissions, list) or not all(
        isinstance(permission, str) for permission in permissions
    ):
        errors.append(
            _error(
                doc,
                tool,
                f"tool {tool_name!r} 'permissions' must be a list of strings",
            )
        )

    confirmation = tool.get("requires_confirmation")
    if confirmation is not None and not isinstance(confirmation, bool):
        errors.append(
            _error(
                doc,
                tool,
                f"tool {tool_name!r} 'requires_confirmation' must be a boolean",
            )
        )
