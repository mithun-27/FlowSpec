"""Tests for the compilation pipeline and the Compiler facade."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from tests.helpers import TOOLS_YAML

from flowspec.compiler.compiler import Compiler
from flowspec.compiler.pipeline import PIPELINE_PASSES, CompilationPipeline
from flowspec.config import CompilerConfig
from flowspec.exceptions import ConfigurationError


def _project(tmp_path: Path, workflow_text: str, tools_text: str | None = TOOLS_YAML):
    """Write a workflow (+ tools) into a temp project directory."""
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(workflow_text, encoding="utf-8")
    if tools_text is not None:
        (tmp_path / "tools.yaml").write_text(tools_text, encoding="utf-8")
    return workflow


def _codes(result) -> list[str]:
    return sorted(diagnostic.code for diagnostic in result.diagnostics)


def test_pipeline_passes_metadata_documents_the_plan() -> None:
    assert [entry[0] for entry in PIPELINE_PASSES] == [f"P{i}" for i in range(13)]
    planned = {name for _, name, status in PIPELINE_PASSES if "planned" in status}
    assert planned == {"Dataflow analysis", "Effect analysis"}


def test_valid_example_compiles_with_ir(invoice_example_dir: Path) -> None:
    result = Compiler().compile(invoice_example_dir / "workflow.yaml")

    assert result.success
    assert result.diagnostics == ()
    assert result.workflow_name == "invoice_processing"
    assert result.error_count == 0

    assert result.ir is not None
    assert result.ir.workflow_name == "invoice_processing"
    assert result.execution_order == ("customer", "invoice", "payment", "send")
    assert [list(stage.steps) for stage in result.stages] == [
        ["customer"],
        ["invoice"],
        ["payment", "send"],
    ]

    assert result.graph is not None
    assert result.graph.step_ids == ("customer", "invoice", "send", "payment")


def test_valid_example_compiles_identically_twice(invoice_example_dir: Path) -> None:
    first = Compiler().compile(invoice_example_dir / "workflow.yaml")
    second = Compiler().compile(invoice_example_dir / "workflow.yaml")

    assert first.diagnostics == second.diagnostics == ()
    assert first.ir is not None and second.ir is not None
    assert first.ir.to_json() == second.ir.to_json()


def test_invalid_example_fails_with_expected_diagnostics(
    invoice_example_dir: Path,
) -> None:
    result = Compiler().compile(invoice_example_dir / "workflow_invalid.yaml")

    assert not result.success
    assert _codes(result) == ["E102", "E201", "E201", "E202", "E304", "E401"]
    assert result.error_count == 6
    assert result.ir is None
    assert result.workflow_name == "invoice_processing_invalid"
    assert result.summary() == "6 errors"


def test_invalid_example_diagnostics_are_stable(invoice_example_dir: Path) -> None:
    first = Compiler().compile(invoice_example_dir / "workflow_invalid.yaml")
    second = Compiler().compile(invoice_example_dir / "workflow_invalid.yaml")

    assert [d.message for d in first.diagnostics] == [d.message for d in second.diagnostics]


def test_missing_workflow_file_is_a_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="file not found"):
        Compiler().compile(tmp_path / "missing.yaml")


def test_missing_tools_file_is_a_configuration_error(tmp_path: Path) -> None:
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n"
        "  inputs:\n    email: {type: string, required: true}\n",
        tools_text=None,
    )
    with pytest.raises(ConfigurationError, match=re.escape("tools.yaml")):
        Compiler().compile(workflow)


def test_yaml_syntax_error_is_an_e001_early_exit(tmp_path: Path) -> None:
    workflow = _project(tmp_path, "version: '1.0'\nworkflow: [unclosed\n")
    result = Compiler().compile(workflow)

    assert not result.success
    assert _codes(result) == ["E001"]
    assert result.workflow_name is None
    assert result.ir is None


def test_bad_reference_syntax_is_an_e001_early_exit(tmp_path: Path) -> None:
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input\n",
    )
    result = Compiler().compile(workflow)

    assert _codes(result) == ["E001"]
    assert result.workflow_name is None
    assert result.ir is None


def test_workflow_structure_error_is_an_e002_early_exit(tmp_path: Path) -> None:
    # No tools.yaml exists in this project: the early exit must happen
    # before the tool schema is ever loaded.
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: w\n  steps: not-a-list\n",
        tools_text=None,
    )
    result = Compiler().compile(workflow)

    assert _codes(result) == ["E002"]
    assert result.workflow_name is None
    assert result.ir is None


def test_tools_structure_error_exits_early_without_e401_cascade(
    tmp_path: Path,
) -> None:
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: w\n  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n",
        tools_text="version: '1.0'\ntools: not-a-mapping\n",
    )
    result = Compiler().compile(workflow)

    # The registry is unusable, so the run stops instead of reporting
    # every tool as E401.
    assert _codes(result) == ["E002"]
    assert result.workflow_name == "w"
    assert result.ir is None


def test_tools_type_errors_continue_but_block_ir(tmp_path: Path) -> None:
    tools = """
version: '1.0'
tools:
  broken:
    inputs:
      x: {type: 'List['}
  get_customer:
    inputs:
      email: {type: string, required: true}
    outputs:
      customer_id: {type: CustomerID}
      email: {type: string}
"""
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: w\n  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n",
        tools_text=tools,
    )
    result = Compiler().compile(workflow)

    # The E205 is reported and the rest of the pipeline still runs over
    # the usable tools — but errors mean no IR.
    assert _codes(result) == ["E205"]
    assert result.workflow_name == "w"
    assert not result.success
    assert result.ir is None


def test_generate_ir_false_yields_success_without_ir(invoice_example_dir: Path) -> None:
    compiler = Compiler(CompilerConfig(generate_ir=False))
    result = compiler.compile(invoice_example_dir / "workflow.yaml")

    assert result.success
    assert result.diagnostics == ()
    assert result.ir is None
    assert result.execution_order == ()
    assert result.graph is not None
    assert [list(stage.steps) for stage in result.stages] == [
        ["customer"],
        ["invoice"],
        ["payment", "send"],
    ]


def test_cyclic_workflow_reports_e301_and_never_produces_ir(tmp_path: Path) -> None:
    tools = """
version: '1.0'
tools:
  ping:
    inputs:
      peer: {type: string, required: true}
    outputs:
      pong: {type: string}
  pong:
    inputs:
      peer: {type: string, required: true}
    outputs:
      pong: {type: string}
"""
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: cyclic\n  steps:\n"
        "    - id: a\n      tool: ping\n"
        "      inputs:\n        peer: $b.pong\n"
        "    - id: b\n      tool: pong\n"
        "      inputs:\n        peer: $a.pong\n",
        tools_text=tools,
    )
    result = Compiler().compile(workflow)

    assert not result.success
    assert _codes(result) == ["E301"]
    assert result.ir is None
    assert result.stages == ()
    assert "a -> b -> a" in result.diagnostics[0].message


def test_disabled_cycle_detection_still_requires_an_order(tmp_path: Path) -> None:
    tools = """
version: '1.0'
tools:
  ping:
    inputs:
      peer: {type: string, required: true}
    outputs:
      pong: {type: string}
  pong:
    inputs:
      peer: {type: string, required: true}
    outputs:
      pong: {type: string}
"""
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: cyclic\n  steps:\n"
        "    - id: a\n      tool: ping\n"
        "      inputs:\n        peer: $b.pong\n"
        "    - id: b\n      tool: pong\n"
        "      inputs:\n        peer: $a.pong\n",
        tools_text=tools,
    )
    compiler = Compiler(CompilerConfig(detect_cycles=False))
    result = compiler.compile(workflow)

    # Cycle diagnostics are suppressed, but the workflow still cannot
    # be scheduled — that fact is reported as E302, never hidden.
    assert _codes(result) == ["E302"]
    assert result.ir is None


def test_explicit_tools_path_is_used(invoice_example_dir: Path, tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        (invoice_example_dir / "workflow.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = Compiler().compile(workflow, tools_path=invoice_example_dir / "tools.yaml")

    assert result.success
    assert result.ir is not None


def test_sibling_tools_json_is_discovered(tmp_path: Path) -> None:
    tools = {
        "version": "1.0",
        "tools": {
            "get_customer": {
                "inputs": {"email": {"type": "string", "required": True}},
                "outputs": {
                    "customer_id": {"type": "CustomerID"},
                    "email": {"type": "string"},
                },
            },
        },
    }
    (tmp_path / "tools.json").write_text(json.dumps(tools), encoding="utf-8")
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        "version: '1.0'\nworkflow:\n  name: w\n  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n",
        encoding="utf-8",
    )

    result = Compiler().compile(workflow)

    assert result.success
    assert result.ir is not None


def test_pipeline_and_facade_agree(invoice_example_dir: Path) -> None:
    facade = Compiler().compile(invoice_example_dir / "workflow.yaml")
    pipeline = CompilationPipeline().run(invoice_example_dir / "workflow.yaml")

    assert facade.diagnostics == pipeline.diagnostics
    assert facade.ir is not None and pipeline.ir is not None
    assert facade.ir.to_json() == pipeline.ir.to_json()
    assert facade.stages == pipeline.stages


def test_workflow_without_steps_compiles(tmp_path: Path) -> None:
    # Edge case: no steps at all still yields a (trivially valid) IR.
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: empty\n  steps: []\n",
    )
    result = Compiler().compile(workflow)

    assert result.success
    assert result.diagnostics == ()
    assert result.ir is not None
    assert result.execution_order == ()


def test_single_step_workflow_compiles(tmp_path: Path) -> None:
    workflow = _project(
        tmp_path,
        "version: '1.0'\nworkflow:\n  name: solo\n  inputs:\n"
        "    email: {type: string, required: true}\n"
        "  steps:\n"
        "    - id: a\n      tool: get_customer\n"
        "      inputs:\n        email: $input.email\n",
    )
    result = Compiler().compile(workflow)

    assert result.success
    assert result.ir is not None
    assert result.execution_order == ("a",)
    assert [list(stage.steps) for stage in result.stages] == [["a"]]
