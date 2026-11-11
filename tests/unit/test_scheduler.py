"""Tests for parallel execution stage scheduling."""

from __future__ import annotations

from pathlib import Path

from flowspec.graph.dependency import DependencyEdge
from flowspec.graph.graph import WorkflowGraph
from flowspec.graph.scheduler import build_execution_stages
from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.yaml_parser import parse_yaml_document
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.semantic.name_resolution import resolve_workflow


def _graph(steps, pairs) -> WorkflowGraph:
    return WorkflowGraph(
        steps,
        [DependencyEdge(from_step=a, to_step=b, output="out", argument="in") for a, b in pairs],
    )


def test_independent_steps_share_one_stage() -> None:
    stages = build_execution_stages(_graph(["b", "a"], []))
    assert stages is not None
    assert len(stages) == 1
    assert stages[0].index == 0
    assert stages[0].steps == ("a", "b")


def test_diamond_graph_stages() -> None:
    graph = _graph(
        ["a", "b", "c", "d"],
        [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")],
    )
    stages = build_execution_stages(graph)
    assert stages is not None
    assert [stage.steps for stage in stages] == [
        ("a",),
        ("b", "c"),
        ("d",),
    ]
    assert [stage.index for stage in stages] == [0, 1, 2]


def test_cyclic_graph_has_no_schedule() -> None:
    graph = _graph(["a", "b"], [("a", "b"), ("b", "a")])
    assert build_execution_stages(graph) is None


def test_empty_graph_yields_no_stages() -> None:
    stages = build_execution_stages(WorkflowGraph([], []))
    assert stages == []


def test_stages_respect_dependencies() -> None:
    # Every step appears exactly once, and always after its predecessors.
    graph = _graph(
        ["a", "b", "c", "d", "e"],
        [("a", "c"), ("b", "c"), ("c", "e"), ("b", "d")],
    )
    stages = build_execution_stages(graph)
    assert stages is not None
    position = {step: stage.index for stage in stages for step in stage.steps}
    for step in graph.step_ids:
        for predecessor in graph.predecessors(step):
            assert position[predecessor] < position[step]


def test_valid_example_stages(invoice_example_dir: Path) -> None:
    workflow_path = invoice_example_dir / "workflow.yaml"
    document = parse_yaml_document(
        workflow_path.read_text(encoding="utf-8"), file=str(workflow_path)
    )
    workflow = build_workflow_ast(document)
    registry, _ = load_tool_schema(invoice_example_dir / "tools.yaml")
    symbols = resolve_workflow(workflow, registry).symbols
    graph = WorkflowGraph.from_workflow(workflow, symbols)

    stages = build_execution_stages(graph)
    assert stages is not None
    assert [stage.steps for stage in stages] == [
        ("customer",),
        ("invoice",),
        ("payment", "send"),
    ]
