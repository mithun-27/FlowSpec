"""Tests for deterministic topological sorting (Kahn)."""

from __future__ import annotations

from pathlib import Path

from flowspec.graph.dependency import DependencyEdge
from flowspec.graph.graph import WorkflowGraph
from flowspec.graph.topological_sort import topological_sort
from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.yaml_parser import parse_yaml_document
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.semantic.name_resolution import resolve_workflow


def _graph(steps, pairs) -> WorkflowGraph:
    return WorkflowGraph(
        steps,
        [DependencyEdge(from_step=a, to_step=b, output="out", argument="in") for a, b in pairs],
    )


def test_empty_graph_sorts_to_empty_list() -> None:
    assert topological_sort(WorkflowGraph([], [])) == []


def test_deterministic_lexicographic_order() -> None:
    graph = _graph(["c", "a", "b"], [("c", "b"), ("c", "a")])
    # Ties broken by sorted order: a before b.
    assert topological_sort(graph) == ["c", "a", "b"]


def test_diamond_graph() -> None:
    graph = _graph(
        ["a", "b", "c", "d"],
        [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")],
    )
    assert topological_sort(graph) == ["a", "b", "c", "d"]


def test_cyclic_graph_returns_none() -> None:
    graph = _graph(["a", "b"], [("a", "b"), ("b", "a")])
    assert topological_sort(graph) is None


def test_self_loop_returns_none() -> None:
    graph = _graph(["a"], [("a", "a")])
    assert topological_sort(graph) is None


def test_valid_example_order(invoice_example_dir: Path) -> None:
    workflow_path = invoice_example_dir / "workflow.yaml"
    document = parse_yaml_document(
        workflow_path.read_text(encoding="utf-8"), file=str(workflow_path)
    )
    workflow = build_workflow_ast(document)
    registry, _ = load_tool_schema(invoice_example_dir / "tools.yaml")
    symbols = resolve_workflow(workflow, registry).symbols
    graph = WorkflowGraph.from_workflow(workflow, symbols)

    order = topological_sort(graph)
    assert order == ["customer", "invoice", "payment", "send"]


def test_sort_is_stable_across_calls() -> None:
    graph = _graph(
        ["a", "b", "c", "d", "e"],
        [("a", "d"), ("b", "d"), ("c", "e")],
    )
    assert (
        topological_sort(graph)
        == topological_sort(graph)
        == [
            "a",
            "b",
            "c",
            "d",
            "e",
        ]
    )
