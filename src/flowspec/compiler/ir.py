"""The versioned FlowSpec intermediate representation (pipeline P12).

A stable, format-independent IR carrying the workflow name and schema
version, explicit input and output types, step contracts with dependency
and type information, tool effect and permission metadata, execution
order and stages, compiler version, and the dependency graph.

Serialization is deterministic: no timestamps, sorted keys, and lists
derived only from the source (declaration order) or sorted explicitly.
Identical inputs and configuration always produce identical JSON.
Invalid workflows are never exported as executable IR.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from flowspec._version import __version__
from flowspec.ast.expressions import describe_expression
from flowspec.ast.workflow import WorkflowNode
from flowspec.graph.graph import WorkflowGraph
from flowspec.graph.scheduler import ExecutionStage
from flowspec.registry.tool_registry import ToolRegistry
from flowspec.typesystem.inference import TypeInference

__all__ = ["IR_VERSION", "IntermediateRepresentation"]

#: The IR schema version — independent of the workflow schema version.
#: Breaking changes to the IR structure bump this number.
IR_VERSION = "1.0"


@dataclass(frozen=True)
class IRWorkflowInput:
    """A declared workflow input in the IR."""

    name: str
    type: str
    required: bool


@dataclass(frozen=True)
class IRWorkflowOutput:
    """A workflow output binding in the IR."""

    name: str
    source: str
    type: str


@dataclass(frozen=True)
class IRStepInput:
    """One supplied tool argument in the IR."""

    argument: str
    source: str
    type: str


@dataclass(frozen=True)
class IRStepOutput:
    """One declared tool output in the IR."""

    name: str
    type: str
    nullable: bool


@dataclass(frozen=True)
class IRStep:
    """One workflow step in the IR: its full compiled contract."""

    id: str
    tool: str
    position: int
    dependencies: tuple[str, ...]
    inputs: tuple[IRStepInput, ...]
    outputs: tuple[IRStepOutput, ...]
    effects: tuple[str, ...]
    permissions: tuple[str, ...]
    requires_confirmation: bool


@dataclass(frozen=True)
class IntermediateRepresentation:
    """The compiled, executable representation of a valid workflow."""

    workflow_name: str
    description: str | None
    schema_version: str
    inputs: tuple[IRWorkflowInput, ...]
    outputs: tuple[IRWorkflowOutput, ...]
    steps: tuple[IRStep, ...]
    order: tuple[str, ...]
    stages: tuple[tuple[str, ...], ...]
    graph: dict[str, object]
    effects: tuple[str, ...]
    permissions: tuple[str, ...]
    ir_version: str = IR_VERSION
    compiler_version: str = __version__

    @classmethod
    def build(
        cls,
        workflow: WorkflowNode,
        registry: ToolRegistry,
        inference: TypeInference,
        graph: WorkflowGraph,
        order: tuple[str, ...],
        stages: list[ExecutionStage] | None,
    ) -> IntermediateRepresentation:
        """Compile a fully validated workflow into its IR.

        Requires every expression to have an inferred type — calling
        this for an invalid workflow raises :class:`InternalError` via
        the inference lookup instead of producing broken IR.
        """
        inputs = _workflow_inputs(workflow)

        steps = tuple(
            IRStep(
                id=step.id,
                tool=step.tool,
                position=position,
                dependencies=graph.predecessors(step.id),
                inputs=tuple(
                    IRStepInput(
                        argument=argument,
                        source=describe_expression(expression),
                        type=inference.of(expression).render(),
                    )
                    for argument, expression in sorted(step.inputs.items())
                ),
                outputs=tuple(
                    IRStepOutput(
                        name=parameter.name,
                        type=parameter.type.render(),
                        nullable=parameter.nullable,
                    )
                    for parameter in registry.require(step.tool).outputs
                ),
                effects=registry.require(step.tool).effects,
                permissions=registry.require(step.tool).permissions,
                requires_confirmation=registry.require(step.tool).requires_confirmation,
            )
            for position, step in enumerate(workflow.steps)
        )

        outputs = tuple(
            IRWorkflowOutput(
                name=output.name,
                source=describe_expression(output.expression),
                type=inference.of(output.expression).render(),
            )
            for output in workflow.outputs.values()
        )

        effects: set[str] = set()
        permissions: set[str] = set()
        for step in workflow.steps:
            tool = registry.require(step.tool)
            effects.update(tool.effects)
            permissions.update(tool.permissions)

        return cls(
            workflow_name=workflow.name,
            description=workflow.description,
            schema_version=workflow.version,
            inputs=inputs,
            outputs=outputs,
            steps=steps,
            order=order,
            stages=tuple(stage.steps for stage in (stages or [])),
            graph=graph.to_dict(),
            effects=tuple(sorted(effects)),
            permissions=tuple(sorted(permissions)),
        )

    def to_dict(self) -> dict[str, object]:
        """A deterministic, JSON-friendly representation of the IR."""
        return {
            "ir_version": self.ir_version,
            "compiler_version": self.compiler_version,
            "workflow": {
                "name": self.workflow_name,
                "description": self.description,
                "schema_version": self.schema_version,
                "inputs": [
                    {
                        "name": item.name,
                        "type": item.type,
                        "required": item.required,
                    }
                    for item in self.inputs
                ],
                "outputs": [
                    {"name": item.name, "source": item.source, "type": item.type}
                    for item in self.outputs
                ],
            },
            "steps": [
                {
                    "id": step.id,
                    "tool": step.tool,
                    "position": step.position,
                    "dependencies": list(step.dependencies),
                    "inputs": [
                        {
                            "argument": item.argument,
                            "source": item.source,
                            "type": item.type,
                        }
                        for item in step.inputs
                    ],
                    "outputs": [
                        {
                            "name": item.name,
                            "type": item.type,
                            "nullable": item.nullable,
                        }
                        for item in step.outputs
                    ],
                    "effects": list(step.effects),
                    "permissions": list(step.permissions),
                    "requires_confirmation": step.requires_confirmation,
                }
                for step in self.steps
            ],
            "execution": {
                "order": list(self.order),
                "stages": [list(stage) for stage in self.stages],
            },
            "graph": self.graph,
            "metadata": {
                "effects": list(self.effects),
                "permissions": list(self.permissions),
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Deterministic JSON: sorted keys, no timestamps."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def _workflow_inputs(workflow: WorkflowNode) -> tuple[IRWorkflowInput, ...]:
    """Workflow inputs in declaration order, with parsed types.

    Valid workflows always parse here — name resolution already
    rejected malformed input type expressions (E205).
    """
    from flowspec.typesystem.parser import parse_type

    return tuple(
        IRWorkflowInput(
            name=input_node.name,
            type=parse_type(input_node.type_name).render(),
            required=input_node.required,
        )
        for input_node in workflow.inputs.values()
    )
