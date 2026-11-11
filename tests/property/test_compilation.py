"""Property-based tests for compilation (Hypothesis).

Two properties:

1. Every workflow the generator can build from the fixed test registry —
   every required tool argument bound to a type-compatible, already
   available source — compiles cleanly, and its execution plan respects
   the generated dependencies: the topological order puts producers
   before consumers, the execution stages partition all steps, and every
   dependency lands in a strictly earlier stage. Compilation is also
   deterministic for the same input.

2. For arbitrary directed acyclic graphs, ``topological_sort`` respects
   every edge and ``build_execution_stages`` partitions the nodes with
   every edge crossing from an earlier stage to a later one.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from tests.helpers import TOOLS_YAML

from flowspec.compiler.compiler import Compiler
from flowspec.compiler.result import CompilationResult
from flowspec.graph.dependency import DependencyEdge
from flowspec.graph.graph import WorkflowGraph
from flowspec.graph.scheduler import build_execution_stages
from flowspec.graph.topological_sort import topological_sort

# The fixed registry every generated workflow is compiled against. Only
# the shapes matter here: required inputs, optional inputs, outputs, and
# their declared types (mirrors tests.helpers.TOOLS_YAML).
_REQUIRED_INPUTS: dict[str, dict[str, str]] = {
    "get_customer": {"email": "string"},
    "create_invoice": {"customer_id": "CustomerID", "amount": "float"},
    "send_invoice": {"invoice_id": "InvoiceID"},
    "update_payment_status": {"payment_id": "PaymentID", "status": "string"},
}
_OPTIONAL_INPUTS: dict[str, dict[str, str]] = {
    "send_invoice": {"cc": "string"},
}
_TOOL_OUTPUTS: dict[str, dict[str, str]] = {
    "get_customer": {"customer_id": "CustomerID", "email": "string"},
    "create_invoice": {"invoice_id": "InvoiceID", "payment_id": "PaymentID"},
    "send_invoice": {"status": "string"},
    "update_payment_status": {"updated": "boolean"},
}


def _producer_of(source: str) -> str | None:
    """The step id a ``$step.output`` reference draws from, if any."""
    if source.startswith("$input."):
        return None
    return source[1:].split(".", 1)[0]


@st.composite
def valid_workflows(draw: st.DrawFn) -> tuple[str, dict[str, set[str]]]:
    """A workflow that must compile: type-safe by construction.

    Returns the workflow YAML text and the true dependency map (each step
    id to the set of step ids whose outputs it consumes).
    """
    pool: dict[str, list[str]] = {
        "string": ["$input.email"],
        "float": ["$input.amount"],
    }
    dependencies: dict[str, set[str]] = {}
    lines = [
        "version: '1.0'",
        "",
        "workflow:",
        "  name: generated_workflow",
        "",
        "  inputs:",
        "    email:",
        "      type: string",
        "      required: true",
        "    amount:",
        "      type: float",
        "      required: true",
        "",
        "  steps:",
    ]
    for index in range(draw(st.integers(min_value=1, max_value=8))):
        candidates = sorted(
            tool
            for tool, required in _REQUIRED_INPUTS.items()
            if all(type_name in pool for type_name in required.values())
        )
        tool = draw(st.sampled_from(candidates))
        step_id = f"s{index}"
        dependencies.setdefault(step_id, set())
        lines.append(f"    - id: {step_id}")
        lines.append(f"      tool: {tool}")
        lines.append("      inputs:")
        for argument, type_name in _REQUIRED_INPUTS[tool].items():
            source = draw(st.sampled_from(pool[type_name]))
            producer = _producer_of(source)
            if producer is not None:
                dependencies[step_id].add(producer)
            lines.append(f"        {argument}: {source}")
        for argument, type_name in _OPTIONAL_INPUTS.get(tool, {}).items():
            if type_name in pool and draw(st.booleans()):
                source = draw(st.sampled_from(pool[type_name]))
                producer = _producer_of(source)
                if producer is not None:
                    dependencies[step_id].add(producer)
                lines.append(f"        {argument}: {source}")
        for output, out_type in _TOOL_OUTPUTS[tool].items():
            pool.setdefault(out_type, []).append(f"${step_id}.{output}")
        lines.append("")

    sources = [source for values in pool.values() for source in values]
    chosen = draw(st.sets(st.integers(min_value=0, max_value=len(sources) - 1)))
    if chosen:
        lines.append("  outputs:")
        for position, source_index in enumerate(sorted(chosen)):
            lines.append(f"    o{position}: {sources[source_index]}")

    return "\n".join(lines) + "\n", dependencies


def _compile_generated(workflow_text: str) -> tuple[CompilationResult, CompilationResult]:
    """Compile a generated workflow twice against the fixed registry."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "tools.yaml").write_text(TOOLS_YAML, encoding="utf-8")
        (root / "workflow.yaml").write_text(workflow_text, encoding="utf-8")
        first = Compiler().compile(root / "workflow.yaml", root / "tools.yaml")
        second = Compiler().compile(root / "workflow.yaml", root / "tools.yaml")
    return first, second


@settings(max_examples=50, deadline=None)
@given(workflow=valid_workflows())
def test_valid_workflows_compile_with_respecting_execution_plans(
    workflow: tuple[str, dict[str, set[str]]],
) -> None:
    workflow_text, dependencies = workflow
    result, again = _compile_generated(workflow_text)

    assert result.success, result.diagnostics
    assert result.diagnostics == ()
    assert result.ir is not None

    order = list(result.execution_order)
    assert sorted(order) == sorted(dependencies)
    position = {step_id: index for index, step_id in enumerate(order)}
    for consumer, producers in dependencies.items():
        for producer in producers:
            assert position[producer] < position[consumer]

    stages = [list(stage.steps) for stage in result.stages]
    assert sorted(step for stage in stages for step in stage) == sorted(dependencies)
    stage_of = {step_id: index for index, stage in enumerate(stages) for step_id in stage}
    for consumer, producers in dependencies.items():
        for producer in producers:
            assert stage_of[producer] < stage_of[consumer]

    assert again.ir is not None
    assert result.ir.to_json() == again.ir.to_json()


@st.composite
def random_dags(
    draw: st.DrawFn,
) -> tuple[list[str], list[tuple[int, int]], WorkflowGraph]:
    """A random DAG: nodes ``n0..n{k-1}`` and edges from lower to higher."""
    node_count = draw(st.integers(min_value=1, max_value=12))
    nodes = [f"n{index}" for index in range(node_count)]
    pairs: set[tuple[int, int]] = set()
    if node_count >= 2:
        drawn = draw(
            st.sets(
                st.tuples(
                    st.integers(min_value=0, max_value=node_count - 1),
                    st.integers(min_value=0, max_value=node_count - 1),
                ),
                max_size=60,
            )
        )
        pairs = {(i, j) for i, j in drawn if i < j}
    edges = [
        DependencyEdge(
            from_step=nodes[i],
            to_step=nodes[j],
            output="value",
            argument="input",
        )
        for i, j in sorted(pairs)
    ]
    return nodes, sorted(pairs), WorkflowGraph(nodes, edges)


@settings(max_examples=100, deadline=None)
@given(dag=random_dags())
def test_topological_sort_and_stages_respect_every_edge(
    dag: tuple[list[str], list[tuple[int, int]], WorkflowGraph],
) -> None:
    nodes, pairs, graph = dag

    order = topological_sort(graph)
    assert order is not None
    assert sorted(order) == sorted(nodes)
    position = {step_id: index for index, step_id in enumerate(order)}
    for i, j in pairs:
        assert position[nodes[i]] < position[nodes[j]]

    stages = build_execution_stages(graph)
    assert stages is not None
    partition = [step for stage in stages for step in stage.steps]
    assert sorted(partition) == sorted(nodes)
    stage_of = {step_id: index for index, stage in enumerate(stages) for step_id in stage.steps}
    for i, j in pairs:
        assert stage_of[nodes[i]] < stage_of[nodes[j]]
