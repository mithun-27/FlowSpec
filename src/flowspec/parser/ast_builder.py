"""AST construction from parsed workflow documents.

Transforms structurally validated documents into the format-independent
AST defined in :mod:`flowspec.ast`, preserving source locations from the
parser's location table.

Expression syntax (v0.1.0): ``$input.name`` workflow input references,
``$step.output`` step output references, and primitive literals. Any other
``$``-form is a syntax error (E001); nested property access is not
supported yet.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from typing import Any

from flowspec.ast.expressions import (
    ExpressionNode,
    InputReferenceNode,
    LiteralNode,
    StepReferenceNode,
)
from flowspec.ast.nodes import SourceLocation
from flowspec.ast.workflow import OutputNode, ToolCallNode, WorkflowInputNode, WorkflowNode
from flowspec.exceptions import DocumentStructureError, SourceSyntaxError
from flowspec.parser.document import Document

__all__ = ["build_expression", "build_workflow_ast"]


def build_expression(value: Any, location: SourceLocation) -> ExpressionNode:
    """Build an expression node from a scalar workflow value.

    Raises :class:`SourceSyntaxError` (E001) for invalid ``$``-reference
    syntax and :class:`DocumentStructureError` (E002) for non-scalars.
    """
    if isinstance(value, str) and value.startswith("$"):
        return _build_reference(value, location)
    if _is_scalar(value):
        return LiteralNode(value=value, location=location)
    raise DocumentStructureError(
        f"expression must be a scalar, received {type(value).__name__}",
        location=location,
    )


def _is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def _build_reference(value: str, location: SourceLocation) -> ExpressionNode:
    parts = value.split(".")
    head = parts[0]

    if head == "$input":
        if len(parts) != 2 or not parts[1]:
            raise SourceSyntaxError(
                f"invalid workflow input reference {value!r}: expected '$input.name'",
                location=location,
            )
        return InputReferenceNode(name=parts[1], location=location)

    if head.startswith("$") and len(head) > 1:
        if len(parts) != 2 or not parts[1]:
            raise SourceSyntaxError(
                f"invalid step reference {value!r}: expected '$step.output'",
                location=location,
            )
        return StepReferenceNode(step=head[1:], output=parts[1], location=location)

    raise SourceSyntaxError(
        f"invalid reference {value!r}: expected '$input.name' or '$step.output'",
        location=location,
    )


def build_workflow_ast(doc: Document) -> WorkflowNode:
    """Build a :class:`WorkflowNode` from a validated workflow document.

    Assumes :func:`flowspec.parser.validator.validate_workflow_document`
    reported no errors; anything unexpected raises
    :class:`DocumentStructureError` (E002) rather than guessing.
    """
    data = doc.data
    if not isinstance(data, dict):
        raise DocumentStructureError(
            "workflow document root must be a mapping",
            location=doc.located(data),
        )

    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        raise DocumentStructureError(
            "document is missing the required 'workflow' mapping",
            location=doc.located(data),
        )

    name = workflow.get("name")
    if not isinstance(name, str) or not name:
        raise DocumentStructureError(
            "workflow must declare a non-empty 'name' string",
            location=doc.located(workflow),
        )

    workflow_location = (
        doc.located(workflow) or doc.located(data) or SourceLocation.unknown(doc.file)
    )

    inputs = {}
    for input_name, spec in (workflow.get("inputs") or {}).items():
        if not isinstance(spec, dict):
            raise DocumentStructureError(
                f"workflow input {input_name!r} must be a mapping",
                location=doc.located(workflow.get("inputs")) or workflow_location,
            )
        inputs[input_name] = WorkflowInputNode(
            name=input_name,
            type_name=_required_string(spec, "type"),
            required=spec.get("required", True),
            location=doc.located(spec) or workflow_location,
        )

    steps = []
    raw_steps = workflow.get("steps") or []
    for raw_step in raw_steps:
        if not isinstance(raw_step, dict):
            raise DocumentStructureError(
                "workflow step must be a mapping",
                location=doc.located(raw_steps) or workflow_location,
            )
        steps.append(_build_step(doc, raw_step, workflow_location))

    outputs = {}
    raw_outputs = workflow.get("outputs") or {}
    for output_name, raw_expression in raw_outputs.items():
        expression_location = doc.located(raw_outputs) or workflow_location
        outputs[output_name] = OutputNode(
            name=output_name,
            expression=build_expression(raw_expression, expression_location),
            location=expression_location,
        )

    return WorkflowNode(
        name=name,
        version=data.get("version", "1.0"),
        description=workflow.get("description"),
        inputs=inputs,
        steps=tuple(steps),
        outputs=outputs,
        location=workflow_location,
    )


def _build_step(doc: Document, raw_step: dict, fallback: SourceLocation) -> ToolCallNode:
    step_location = doc.located(raw_step) or fallback
    step_inputs = raw_step.get("inputs") or {}
    if not isinstance(step_inputs, dict):
        raise DocumentStructureError(
            f"step {raw_step.get('id', '?')!r} 'inputs' must be a mapping",
            location=step_location,
        )
    inputs_location = doc.located(step_inputs) or step_location

    expressions = {}
    for argument, raw_expression in step_inputs.items():
        expressions[argument] = build_expression(raw_expression, inputs_location)

    step_id = _required_string(raw_step, "id")
    return ToolCallNode(
        id=step_id,
        tool=_required_string(raw_step, "tool"),
        inputs=expressions,
        location=step_location,
    )


def _required_string(mapping: dict, key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise DocumentStructureError(f"expected a non-empty string for {key!r}")
    return value
