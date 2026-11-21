"""Tests for reachability (dead-step) analysis and its E303 diagnostics."""

from __future__ import annotations

from pathlib import Path

from tests.helpers import TOOLS_YAML, minimal_registry, registry_from_text, workflow_from_text

from flowspec.ast.workflow import WorkflowNode
from flowspec.compiler.compiler import Compiler
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.models import Severity
from flowspec.graph.dependency import DependencyEdge
from flowspec.graph.graph import WorkflowGraph
from flowspec.graph.reachability import analyze_reachability, unreachable_steps


def _edge(from_step: str, to_step: str) -> DependencyEdge:
    return DependencyEdge(from_step=from_step, to_step=to_step, output="out", argument="in")


def _workflow(outputs: str, steps: str) -> WorkflowNode:
    text = "version: '1.0'\n\nworkflow:\n  name: reachability_demo\n\n  steps:\n" + steps
    if outputs:
        text += "\n  outputs:\n" + outputs
    return workflow_from_text(text)


_STEPS = """    - id: a
      tool: get_customer
      inputs:
        email: $input.email

    - id: b
      tool: create_invoice
      inputs:
        customer_id: $a.customer_id
        amount: $input.amount

    - id: dead
      tool: send_invoice
      inputs:
        invoice_id: $input.email
"""

_EFFECTFUL_TOOLS = """
version: '1.0'
tools:
  reader:
    outputs:
      value: {type: string}
    effects: [read]
  writer:
    inputs:
      value: {type: string}
    effects: [write]
"""

_EFFECTFUL_STEPS = """    - id: read
      tool: reader
      inputs: {}

    - id: write
      tool: writer
      inputs:
        value: $read.value

    - id: sink
      tool: reader
      inputs: {}
"""


def test_unreachable_steps_follow_outputs_and_dependencies() -> None:
    workflow = _workflow("    result: $b.invoice_id\n", _STEPS)
    graph = WorkflowGraph(("a", "b", "dead"), (_edge("a", "b"),))

    assert unreachable_steps(graph, workflow, minimal_registry()) == ("dead",)


def test_effectful_steps_are_roots_even_when_not_output_referenced() -> None:
    workflow = _workflow("    result: $sink.value\n", _EFFECTFUL_STEPS)
    graph = WorkflowGraph(("read", "write", "sink"), (_edge("read", "write"),))

    # 'write' is a root because of its side effect; 'read' feeds it.
    assert unreachable_steps(graph, workflow, registry_from_text(_EFFECTFUL_TOOLS)) == ()


def test_read_only_steps_without_consumer_are_dead() -> None:
    workflow = _workflow("    result: $sink.value\n", _EFFECTFUL_STEPS)
    graph = WorkflowGraph(("read", "write", "sink"), (_edge("read", "write"),))
    read_only_registry = registry_from_text(
        _EFFECTFUL_TOOLS.replace("effects: [write]", "effects: [read]")
    )

    assert unreachable_steps(graph, workflow, read_only_registry) == ("read", "write")


def test_analyze_reachability_emits_structured_e303() -> None:
    workflow = _workflow("    result: $b.invoice_id\n", _STEPS)
    graph = WorkflowGraph(("a", "b", "dead"), (_edge("a", "b"),))

    diagnostics = analyze_reachability(graph, workflow, minimal_registry())

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == ErrorCodes.UNREACHABLE_STEP
    assert diagnostic.severity == Severity.ERROR
    assert diagnostic.step == "dead"
    assert diagnostic.workflow == "reachability_demo"
    assert diagnostic.location is not None and diagnostic.location.line > 0
    assert len(diagnostic.suggestions) == 2
    assert diagnostics == analyze_reachability(graph, workflow, minimal_registry())


def test_analyze_reachability_is_empty_for_fully_used_workflow() -> None:
    workflow = _workflow("    result: $b.invoice_id\n", _STEPS)
    graph = WorkflowGraph(("a", "b"), (_edge("a", "b"),))

    assert analyze_reachability(graph, workflow, minimal_registry()) == ()


def test_pipeline_blocks_ir_for_dead_step(tmp_path: Path) -> None:
    workflow_text = """\
version: '1.0'

workflow:
  name: dead_step_demo
  inputs:
    email: {type: string, required: true}
    amount: {type: float, required: true}
  steps:
    - id: customer
      tool: get_customer
      inputs:
        email: $input.email
    - id: invoice
      tool: create_invoice
      inputs:
        customer_id: $customer.customer_id
        amount: $input.amount
  outputs:
    customer_id: $customer.customer_id
"""
    (tmp_path / "tools.yaml").write_text(TOOLS_YAML, encoding="utf-8")
    (tmp_path / "workflow.yaml").write_text(workflow_text, encoding="utf-8")

    result = Compiler().compile(tmp_path / "workflow.yaml")

    assert not result.success
    assert result.ir is None
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["E303"]
    assert result.diagnostics[0].step == "invoice"
