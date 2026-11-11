"""Tests for the constraint validation engine and its E601 diagnostics."""

from __future__ import annotations

from pathlib import Path

from tests.helpers import minimal_registry, registry_from_text, workflow_from_text

from flowspec.analysis.constraints import CONSTRAINT_KINDS, ConstraintEngine
from flowspec.analysis.static import StaticAnalyzer
from flowspec.graph.dependency import DependencyEdge
from flowspec.graph.graph import WorkflowGraph
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.semantic.name_resolution import resolve_workflow
from flowspec.typesystem.inference import infer_expression_types

_EMAIL_INPUTS = "  inputs:\n    email: {type: string, required: true}\n"


def _state(text: str, registry=None):
    """Compile workflow text through the real passes to engine input state.

    Returns (workflow, symbols, registry, inference, graph). Diagnostics
    from the passes are irrelevant here — the engine is an independent
    net over the compiled state.
    """
    workflow = workflow_from_text(text)
    registry = registry or minimal_registry()
    symbols = resolve_workflow(workflow, registry).symbols
    inference, _ = infer_expression_types(workflow, symbols)
    graph = WorkflowGraph.from_workflow(workflow, symbols)
    return workflow, symbols, registry, inference, graph


def _evaluate(text: str, registry=None, graph=None):
    workflow, symbols, resolved_registry, inference, default_graph = _state(text, registry)
    engine = ConstraintEngine()
    return engine.evaluate(workflow, symbols, resolved_registry, inference, graph or default_graph)


def _kinds(report):
    return [constraint.kind for constraint in report.constraints]


def _violation_kinds(report):
    return [violation.constraint.kind for violation in report.violations]


def test_valid_example_is_fully_satisfied(invoice_example_dir: Path) -> None:
    workflow = workflow_from_text(
        (invoice_example_dir / "workflow.yaml").read_text(encoding="utf-8")
    )
    registry, _ = load_tool_schema(invoice_example_dir / "tools.yaml")
    symbols = resolve_workflow(workflow, registry).symbols
    inference, _ = infer_expression_types(workflow, symbols)
    graph = WorkflowGraph.from_workflow(workflow, symbols)

    report = ConstraintEngine().evaluate(workflow, symbols, registry, inference, graph)

    assert report.satisfied
    assert report.violations == ()
    # Every applicable constraint kind is compiled over the example.
    # NonNullRequired only compiles when a nullable source meets a
    # non-Optional target — the valid example has none.
    assert set(_kinds(report)) == set(CONSTRAINT_KINDS) - {"NonNullRequired"}
    assert report.constraints  # a non-trivial constraint set


def test_evaluation_is_deterministic(invoice_example_dir: Path) -> None:
    workflow = workflow_from_text(
        (invoice_example_dir / "workflow.yaml").read_text(encoding="utf-8")
    )
    registry, _ = load_tool_schema(invoice_example_dir / "tools.yaml")
    symbols = resolve_workflow(workflow, registry).symbols
    inference, _ = infer_expression_types(workflow, symbols)
    graph = WorkflowGraph.from_workflow(workflow, symbols)
    engine = ConstraintEngine()

    first = engine.evaluate(workflow, symbols, registry, inference, graph)
    second = engine.evaluate(workflow, symbols, registry, inference, graph)

    assert first == second


def test_missing_required_input_violates_required_input() -> None:
    text = "version: '1.0'\nworkflow:\n  name: w\n  steps:\n    - id: a\n      tool: get_customer\n"
    report = _evaluate(text)

    assert _violation_kinds(report) == ["RequiredInput"]
    violation = report.violations[0]
    assert "email" in violation.constraint.subject
    assert violation.expected == "email"
    assert violation.received == "not supplied"


def test_unknown_input_reference_violates_reference_exists() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.nope\n"
    )
    report = _evaluate(text)

    assert _violation_kinds(report) == ["ReferenceExists"]
    assert report.violations[0].received == "$input.nope"


def test_unknown_step_output_reference_violates_reference_exists() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.nope\n"
        "        amount: 1.0\n"
    )
    report = _evaluate(text)

    assert _violation_kinds(report) == ["ReferenceExists"]
    assert report.violations[0].received == "$customer.nope"


def test_type_mismatch_violates_type_compatibility() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        '        amount: "not-a-number"\n'
    )
    report = _evaluate(text)

    assert _violation_kinds(report) == ["TypeCompatibility"]
    violation = report.violations[0]
    assert violation.expected == "float"
    assert violation.received == "string"


def test_null_source_violates_non_null_required_exactly_once() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: null\n"
    )
    report = _evaluate(text)

    # One violation, owned by NonNullRequired — TypeCompatibility must not
    # double-report the same argument.
    assert _violation_kinds(report) == ["NonNullRequired"]
    violation = report.violations[0]
    assert violation.received == "null"
    assert violation.expected == "string"


def test_nullable_source_violates_non_null_required() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n    email: {type: 'Optional[string]'}\n"
        "  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
    )
    report = _evaluate(text)

    assert _violation_kinds(report) == ["NonNullRequired"]
    assert report.violations[0].received == "Optional[string]"


def test_nullable_parameter_accepts_nullable_source() -> None:
    tools = """
version: '1.0'
tools:
  maybe_log:
    inputs:
      message: {type: string, nullable: true}
    outputs:
      done: {type: boolean}
"""
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n"
        "  inputs:\n    email: {type: 'Optional[string]'}\n"
        "  steps:\n"
        "    - id: a\n      tool: maybe_log\n"
        "      inputs:\n        message: $input.email\n"
    )
    report = _evaluate(text, registry=registry_from_text(tools))

    assert _violation_kinds(report) == []
    assert report.satisfied


def test_missing_graph_edge_violates_dependency_exists() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "    - id: invoice\n      tool: create_invoice\n"
        "      inputs:\n"
        "        customer_id: $customer.customer_id\n"
        "        amount: 1.0\n"
    )
    # Same steps, but the graph is missing the customer -> invoice edge.
    edgeless = WorkflowGraph(["customer", "invoice"], [])
    report = _evaluate(text, graph=edgeless)

    assert _violation_kinds(report) == ["DependencyExists"]
    assert "customer -> invoice" in report.violations[0].reason


def test_cyclic_graph_violates_dependency_acyclic() -> None:
    def edge(a: str, b: str) -> DependencyEdge:
        return DependencyEdge(from_step=a, to_step=b, output="out", argument="in")

    cyclic = WorkflowGraph(["a", "b"], [edge("a", "b"), edge("b", "a")])
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
    )
    # The cyclic graph is supplied directly; the workflow itself is fine.
    report = _evaluate(text, graph=cyclic)

    assert _violation_kinds(report) == ["DependencyAcyclic"]
    assert "a -> b -> a" in report.violations[0].reason


def test_unknown_workflow_output_violates_output_exists() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n" + _EMAIL_INPUTS + "  steps:\n"
        "    - id: customer\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "  outputs:\n    thing: $customer.nope\n"
    )
    report = _evaluate(text)

    assert _violation_kinds(report) == ["OutputExists"]
    assert report.violations[0].received == "$customer.nope"


def test_unknown_tool_steps_are_skipped() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: ghost\n      tool: delete_customer\n"
        "      inputs:\n        whatever: $input.nope\n"
    )
    report = _evaluate(text)

    # No contract to constrain against; only the graph-level constraint compiles.
    assert _violation_kinds(report) == []
    assert "DependencyAcyclic" in _kinds(report)
    assert not any(constraint.step == "ghost" for constraint in report.constraints)


def test_multiple_violations_are_ordered_deterministically() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "    - id: b\n      tool: get_customer\n"
        "      inputs:\n        email: null\n"
    )
    first = _evaluate(text)
    second = _evaluate(text)

    assert first == second
    # Step order drives compilation order: a's RequiredInput, then b's.
    assert _violation_kinds(first) == ["RequiredInput", "NonNullRequired"]


def test_static_analyzer_converts_violations_to_e601() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: null\n"
    )
    workflow, symbols, registry, inference, graph = _state(text)

    diagnostics = StaticAnalyzer().analyze(workflow, symbols, registry, inference, graph)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == "E601"
    assert diagnostic.is_error
    assert diagnostic.workflow == "w"
    assert diagnostic.step == "a"
    assert "NonNullRequired" in diagnostic.message
    assert diagnostic.expected == "string"
    assert diagnostic.received == "null"
