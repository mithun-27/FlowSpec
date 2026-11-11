"""Tests for the workflow dependency graph."""

from __future__ import annotations

from pathlib import Path

from tests.helpers import minimal_registry, workflow_from_text

from flowspec.graph.dependency import DependencyEdge, extract_dependencies
from flowspec.graph.graph import WorkflowGraph
from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.yaml_parser import parse_yaml_document
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.semantic.name_resolution import resolve_workflow


def _edge(from_step: str, to_step: str, output: str = "out", argument: str = "in"):
    return DependencyEdge(from_step=from_step, to_step=to_step, output=output, argument=argument)


def test_construction_and_adjacency() -> None:
    graph = WorkflowGraph(
        ["a", "b", "c", "d"],
        [_edge("a", "b"), _edge("a", "c"), _edge("b", "d"), _edge("c", "d")],
    )
    assert len(graph) == 4
    assert graph.step_ids == ("a", "b", "c", "d")
    assert "a" in graph and "zz" not in graph
    assert graph.has_step("d")
    assert graph.successors("a") == ("b", "c")
    assert graph.predecessors("d") == ("b", "c")
    assert graph.in_degree("d") == 2
    assert graph.out_degree("a") == 2
    assert graph.in_degree("a") == 0
    assert graph.has_edge("a", "b")
    assert not graph.has_edge("a", "d")
    assert graph.successors("zz") == ()


def test_duplicate_step_ids_keep_first_declaration() -> None:
    graph = WorkflowGraph(["a", "a", "b"], [_edge("a", "b")])
    assert graph.step_ids == ("a", "b")


def test_edges_touching_unknown_steps_are_ignored() -> None:
    graph = WorkflowGraph(["a"], [_edge("a", "ghost"), _edge("ghost", "a")])
    assert graph.successors("a") == ()
    assert graph.predecessors("a") == ()


def test_to_dict_is_deterministic() -> None:
    graph = WorkflowGraph(
        ["a", "b"],
        [_edge("a", "b", "out2", "in2"), _edge("a", "b", "out1", "in1")],
    )
    serialized = graph.to_dict()
    assert serialized["steps"] == ["a", "b"]
    assert serialized["adjacency"] == {"a": ["b"], "b": []}
    assert [edge["output"] for edge in serialized["edges"]] == ["out1", "out2"]
    assert (
        graph.to_dict()
        == WorkflowGraph(
            ["a", "b"], [_edge("a", "b", "out1", "in1"), _edge("a", "b", "out2", "in2")]
        ).to_dict()
    )


def test_edge_description() -> None:
    edge = _edge("customer", "invoice", "customer_id", "customer_id")
    assert edge.describe == "customer.customer_id -> invoice.customer_id"


def test_from_workflow_on_valid_example(invoice_example_dir: Path) -> None:
    workflow_path = invoice_example_dir / "workflow.yaml"
    document = parse_yaml_document(
        workflow_path.read_text(encoding="utf-8"), file=str(workflow_path)
    )
    workflow = build_workflow_ast(document)
    registry, _ = load_tool_schema(invoice_example_dir / "tools.yaml")
    symbols = resolve_workflow(workflow, registry).symbols

    graph = WorkflowGraph.from_workflow(workflow, symbols)

    assert graph.step_ids == ("customer", "invoice", "send", "payment")
    assert graph.successors("customer") == ("invoice",)
    assert graph.successors("invoice") == ("payment", "send")
    assert graph.successors("payment") == ()
    assert graph.predecessors("payment") == ("invoice",)
    assert graph.in_degree("invoice") == 1
    assert graph.out_degree("invoice") == 2


def test_extract_dependencies_skips_unresolved_references() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $ghost.customer_id\n"
        "        amount: 1.0\n"
    )
    workflow = workflow_from_text(text)
    symbols = resolve_workflow(workflow, minimal_registry()).symbols
    assert extract_dependencies(workflow, symbols) == []


def test_extract_dependencies_keeps_source_order() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        "        amount: 1.0\n"
        "    - id: payment\n      tool: update_payment_status\n"
        "      inputs:\n"
        "        payment_id: $invoice.payment_id\n"
        '        status: "pending"\n'
    )
    workflow = workflow_from_text(text)
    symbols = resolve_workflow(workflow, minimal_registry()).symbols
    edges = extract_dependencies(workflow, symbols)
    assert [(edge.from_step, edge.to_step) for edge in edges] == [
        ("customer", "invoice"),
        ("invoice", "payment"),
    ]
    assert edges[0].location is not None
