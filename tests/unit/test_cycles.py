"""Tests for cycle detection (E301 circular, E104 self-dependency)."""

from __future__ import annotations

from flowspec.diagnostics.models import Severity
from flowspec.graph.cycle_detection import cycle_diagnostics, detect_cycles
from flowspec.graph.dependency import DependencyEdge
from flowspec.graph.graph import WorkflowGraph


def _edge(from_step: str, to_step: str) -> DependencyEdge:
    return DependencyEdge(from_step=from_step, to_step=to_step, output="out", argument="in")


def _graph(steps, pairs) -> WorkflowGraph:
    return WorkflowGraph(steps, [_edge(a, b) for a, b in pairs])


def test_acyclic_graph_has_no_cycles() -> None:
    graph = _graph(
        ["a", "b", "c"],
        [("a", "b"), ("b", "c")],
    )
    assert detect_cycles(graph) == []
    assert cycle_diagnostics(graph) == []


def test_self_dependency_is_e104() -> None:
    graph = _graph(["a"], [("a", "a")])
    cycles = detect_cycles(graph)
    assert len(cycles) == 1
    assert cycles[0].kind == "self"
    assert cycles[0].steps == ("a", "a")

    diagnostics = cycle_diagnostics(graph, workflow="w")
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "E104"
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].step == "a"
    assert "own output" in diagnostics[0].message


def test_two_step_cycle_is_e301_with_path() -> None:
    graph = _graph(["a", "b"], [("a", "b"), ("b", "a")])
    cycles = detect_cycles(graph)
    assert len(cycles) == 1
    assert cycles[0].kind == "circular"
    assert cycles[0].path == "a -> b -> a"

    diagnostics = cycle_diagnostics(graph, workflow="w")
    assert diagnostics[0].code == "E301"
    assert diagnostics[0].severity == Severity.ERROR
    assert "a -> b -> a" in diagnostics[0].message


def test_three_step_cycle_reports_full_path() -> None:
    graph = _graph(
        ["a", "b", "c"],
        [("a", "b"), ("b", "c"), ("c", "a")],
    )
    cycles = detect_cycles(graph)
    assert len(cycles) == 1
    assert cycles[0].path == "a -> b -> c -> a"


def test_multiple_cycles_are_all_reported() -> None:
    graph = _graph(
        ["a", "b", "c", "d"],
        [("a", "b"), ("b", "a"), ("c", "d"), ("d", "c")],
    )
    diagnostics = cycle_diagnostics(graph)
    assert [d.code for d in diagnostics] == ["E301", "E301"]
    paths = sorted(d.message for d in diagnostics)
    assert any("a -> b -> a" in message for message in paths)
    assert any("c -> d -> c" in message for message in paths)


def test_steps_downstream_of_a_cycle_are_not_cycles() -> None:
    graph = _graph(
        ["a", "b", "c"],
        [("a", "b"), ("b", "a"), ("b", "c")],
    )
    diagnostics = cycle_diagnostics(graph)
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "E301"


def test_deep_chain_does_not_recursion_error() -> None:
    steps = [f"s{i}" for i in range(5000)]
    pairs = [(f"s{i}", f"s{i + 1}") for i in range(4999)]
    graph = _graph(steps, pairs)
    assert detect_cycles(graph) == []
