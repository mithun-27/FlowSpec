"""Integration tests for the FlowSpec command-line interface.

Exercises every implemented command over the invoice example and over
temporary projects, and pins the stable exit codes (specification §21)
both for command results (via the in-process runner) and for framework
usage errors (via the real ``main()`` entry point in a subprocess).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from typer.testing import CliRunner

import flowspec
from flowspec.cli import app

runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """A temporary project directory containing the invoice example files."""
    for name in ("workflow.yaml", "workflow_invalid.yaml", "tools.yaml"):
        destination = tmp_path / name
        destination.write_bytes(_example_file(name).read_bytes())
    return tmp_path


def _example_file(name: str) -> Path:
    """A file from the invoice example."""
    return Path(__file__).resolve().parents[2] / "examples" / "invoice_processing" / name


@pytest.fixture
def invoice_project(invoice_example_dir: Path) -> Path:
    """The invoice example directory itself."""
    return invoice_example_dir


@pytest.fixture
def cd_tmp_path(tmp_path: Path) -> Iterator[Path]:
    """Run the test body inside a temporary working directory."""
    original = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(original)


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Invoke the real ``flowspec`` entry point in a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "flowspec.cli", *argv],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _codes(output: str) -> list[str]:
    return sorted(line.split()[0] for line in output.splitlines() if line.startswith("E"))


# --- version --------------------------------------------------------


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output == f"FlowSpec {flowspec.__version__}\n"


# --- compile --------------------------------------------------------


def test_compile_valid_workflow_text(invoice_project: Path) -> None:
    result = runner.invoke(app, ["compile", str(invoice_project / "workflow.yaml")])
    assert result.exit_code == 0
    assert "invoice_processing: compiled successfully" in result.output
    assert "steps: 4" in result.output
    assert "execution order: customer -> invoice -> payment -> send" in result.output
    assert "execution stages: customer, invoice, payment/send" in result.output


def test_compile_valid_workflow_json(invoice_project: Path) -> None:
    result = runner.invoke(
        app, ["compile", str(invoice_project / "workflow.yaml"), "--format", "json"]
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["success"] is True
    assert parsed["workflow"] == "invoice_processing"
    assert parsed["summary"] == "no diagnostics"
    assert parsed["diagnostics"] == []
    assert parsed["ir"]["ir_version"] == "1.0"
    assert parsed["ir"]["execution"]["order"] == [
        "customer",
        "invoice",
        "payment",
        "send",
    ]


def test_compile_invalid_workflow_text(invoice_project: Path) -> None:
    result = runner.invoke(app, ["compile", str(invoice_project / "workflow_invalid.yaml")])
    assert result.exit_code == 1
    assert "invoice_processing_invalid: 6 errors" in result.output
    assert _codes(result.output) == ["E102", "E201", "E201", "E202", "E304", "E401"]


def test_compile_invalid_workflow_json(invoice_project: Path) -> None:
    result = runner.invoke(
        app, ["compile", str(invoice_project / "workflow_invalid.yaml"), "--format", "json"]
    )
    assert result.exit_code == 1
    parsed = json.loads(result.output)
    assert parsed["success"] is False
    assert parsed["ir"] is None
    assert sorted(d["code"] for d in parsed["diagnostics"]) == [
        "E102",
        "E201",
        "E201",
        "E202",
        "E304",
        "E401",
    ]


def test_compile_missing_workflow_is_configuration_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["compile", str(tmp_path / "missing.yaml")])
    assert result.exit_code == 2
    assert "configuration error" in result.output
    assert "file not found" in result.output


def test_compile_missing_tools_is_configuration_error(project_dir: Path) -> None:
    (project_dir / "tools.yaml").unlink()
    result = runner.invoke(app, ["compile", str(project_dir / "workflow.yaml")])
    assert result.exit_code == 2
    assert "tools.yaml" in result.output


def test_compile_rejects_unknown_format(invoice_project: Path) -> None:
    result = runner.invoke(
        app, ["compile", str(invoice_project / "workflow.yaml"), "--format", "yaml"]
    )
    assert result.exit_code == 5
    assert "invalid --format 'yaml'" in result.output


def test_compile_verbose_lists_pipeline_passes(invoice_project: Path) -> None:
    result = runner.invoke(app, ["compile", str(invoice_project / "workflow.yaml"), "--verbose"])
    assert result.exit_code == 0
    assert "compiler passes:" in result.output
    assert "P0 Source loading [implemented]" in result.output
    assert "P12 IR generation [implemented]" in result.output
    assert "effects: external_write, read, write" in result.output
    assert "permissions: customers.read" in result.output


def test_compile_emit_ir_writes_deterministic_json(invoice_project: Path, tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    result = runner.invoke(
        app, ["compile", str(invoice_project / "workflow.yaml"), "--emit-ir", str(first)]
    )
    assert result.exit_code == 0
    assert "wrote IR to" in result.output
    runner.invoke(
        app, ["compile", str(invoice_project / "workflow.yaml"), "--emit-ir", str(second)]
    )
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")

    ir = json.loads(first.read_text(encoding="utf-8"))
    assert ir["ir_version"] == "1.0"
    assert ir["workflow"]["name"] == "invoice_processing"
    assert ir["execution"]["stages"] == [["customer"], ["invoice"], ["payment", "send"]]


def test_compile_emit_ir_refuses_invalid_workflow(invoice_project: Path, tmp_path: Path) -> None:
    destination = tmp_path / "nope.json"
    result = runner.invoke(
        app,
        ["compile", str(invoice_project / "workflow_invalid.yaml"), "--emit-ir", str(destination)],
    )
    assert result.exit_code == 1
    assert not destination.exists()
    assert "no IR to write" in result.output


def test_compile_with_explicit_tools_path(invoice_project: Path, tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        (invoice_project / "workflow.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "compile",
            str(workflow),
            "--tools",
            str(invoice_project / "tools.yaml"),
        ],
    )
    assert result.exit_code == 0
    assert "compiled successfully" in result.output


def test_compile_uses_project_configuration(project_dir: Path) -> None:
    """A flowspec.yaml beside the workflow configures the compilation."""
    (project_dir / "flowspec.yaml").write_text(
        "compiler:\n  generate_ir: false\n", encoding="utf-8"
    )
    result = runner.invoke(app, ["compile", str(project_dir / "workflow.yaml"), "--format", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["success"] is True
    assert parsed["ir"] is None  # IR generation disabled by the project


def test_compile_reports_invalid_project_configuration(project_dir: Path) -> None:
    (project_dir / "flowspec.yaml").write_text("compiler:\n  nonsense: true\n", encoding="utf-8")
    result = runner.invoke(app, ["compile", str(project_dir / "workflow.yaml")])
    assert result.exit_code == 2
    assert "unknown compiler configuration keys" in result.output


def test_compile_json_output_is_deterministic(invoice_project: Path) -> None:
    first = runner.invoke(
        app, ["compile", str(invoice_project / "workflow.yaml"), "--format", "json"]
    )
    again = runner.invoke(
        app, ["compile", str(invoice_project / "workflow.yaml"), "--format", "json"]
    )
    assert first.exit_code == again.exit_code == 0
    assert first.output == again.output


# --- parse ----------------------------------------------------------


def test_parse_valid_workflow(invoice_project: Path) -> None:
    result = runner.invoke(app, ["parse", str(invoice_project / "workflow.yaml")])
    assert result.exit_code == 0
    assert "workflow: invoice_processing" in result.output
    assert "description: Complete invoice processing workflow." in result.output
    assert "  email: string (required)" in result.output
    assert "  customer [get_customer]" in result.output
    assert "    email <- $input.email" in result.output
    assert "  payment [update_payment_status]" in result.output
    assert '    status <- "pending"' in result.output
    assert "  invoice_id <- $invoice.invoice_id" in result.output


def test_parse_syntax_error_exits_one(tmp_path: Path) -> None:
    broken = tmp_path / "workflow.yaml"
    broken.write_text("version: '1.0'\nworkflow: [unclosed\n", encoding="utf-8")
    result = runner.invoke(app, ["parse", str(broken)])
    assert result.exit_code == 1
    assert "E001" in result.output


def test_parse_structure_error_exits_one(tmp_path: Path) -> None:
    broken = tmp_path / "workflow.yaml"
    broken.write_text(
        "version: '1.0'\nworkflow:\n  name: w\n  steps: not-a-list\n", encoding="utf-8"
    )
    result = runner.invoke(app, ["parse", str(broken)])
    assert result.exit_code == 1
    assert "E002" in result.output


def test_parse_missing_file_exits_two(tmp_path: Path) -> None:
    result = runner.invoke(app, ["parse", str(tmp_path / "missing.yaml")])
    assert result.exit_code == 2


def test_parse_bad_reference_syntax_exits_one(tmp_path: Path) -> None:
    broken = tmp_path / "workflow.yaml"
    broken.write_text(
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: t\n      inputs:\n        x: $input\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["parse", str(broken)])
    assert result.exit_code == 1
    assert "E001" in result.output


# --- inspect --------------------------------------------------------


def test_inspect_registry(invoice_project: Path) -> None:
    result = runner.invoke(app, ["inspect", str(invoice_project / "tools.yaml")])
    assert result.exit_code == 0
    assert "4 tool(s)" in result.output
    assert "get_customer: Find a customer using email." in result.output
    assert "  input  email: string (required)" in result.output
    assert "  output customer_id: CustomerID" in result.output
    assert "  effects: read" in result.output
    assert "  permissions: customers.read" in result.output


def test_inspect_reports_contract_errors(tmp_path: Path) -> None:
    tools = tmp_path / "tools.yaml"
    tools.write_text(
        "version: '1.0'\ntools:\n  broken:\n    inputs:\n      x: {type: 'List['}\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["inspect", str(tools)])
    assert result.exit_code == 1
    assert "E205" in result.output


def test_inspect_missing_file_exits_two(tmp_path: Path) -> None:
    result = runner.invoke(app, ["inspect", str(tmp_path / "missing.yaml")])
    assert result.exit_code == 2


# --- explain --------------------------------------------------------


def test_explain_valid_workflow(invoice_project: Path) -> None:
    result = runner.invoke(app, ["explain", str(invoice_project / "workflow.yaml")])
    assert result.exit_code == 0
    assert "workflow: invoice_processing" in result.output
    assert "  0. customer [get_customer]" in result.output
    assert "     depends on: -" in result.output
    assert "     email <- $input.email : string" in result.output
    assert "     outputs customer_id : CustomerID" in result.output
    assert "  1. invoice [create_invoice]" in result.output
    assert "     depends on: customer" in result.output
    assert "     customer_id <- $customer.customer_id : CustomerID" in result.output
    assert "workflow outputs:" in result.output
    assert "  invoice_id <- $invoice.invoice_id : InvoiceID" in result.output
    assert "  3. payment, send" in result.output


def test_explain_invalid_workflow_exits_one(invoice_project: Path) -> None:
    result = runner.invoke(app, ["explain", str(invoice_project / "workflow_invalid.yaml")])
    assert result.exit_code == 1
    assert "explain requires a workflow that compiles cleanly" in result.output
    assert "E401" in result.output


# --- export ---------------------------------------------------------


def test_export_writes_ir_to_stdout(invoice_project: Path) -> None:
    result = runner.invoke(app, ["export", str(invoice_project / "workflow.yaml")])
    assert result.exit_code == 0
    ir = json.loads(result.output)
    assert ir["ir_version"] == "1.0"
    assert ir["execution"]["order"] == ["customer", "invoice", "payment", "send"]


def test_export_writes_ir_to_file(invoice_project: Path, tmp_path: Path) -> None:
    destination = tmp_path / "ir.json"
    result = runner.invoke(
        app, ["export", str(invoice_project / "workflow.yaml"), "--output", str(destination)]
    )
    assert result.exit_code == 0
    assert "wrote IR to" in result.output
    ir = json.loads(destination.read_text(encoding="utf-8"))
    assert ir["workflow"]["name"] == "invoice_processing"


def test_export_invalid_workflow_exits_one(invoice_project: Path) -> None:
    result = runner.invoke(app, ["export", str(invoice_project / "workflow_invalid.yaml")])
    assert result.exit_code == 1
    assert "no IR to export" in result.output


def test_export_matches_compile_emit_ir(invoice_project: Path, tmp_path: Path) -> None:
    """``export`` and ``compile --emit-ir`` produce the same artifact."""
    emitted = tmp_path / "emitted.json"
    runner.invoke(
        app, ["compile", str(invoice_project / "workflow.yaml"), "--emit-ir", str(emitted)]
    )
    exported = runner.invoke(app, ["export", str(invoice_project / "workflow.yaml")])
    assert json.loads(exported.output) == json.loads(emitted.read_text(encoding="utf-8"))


# --- init -----------------------------------------------------------


def test_init_creates_verified_project(cd_tmp_path: Path) -> None:
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    for name in ("flowspec.yaml", "tools.yaml", "workflow.yaml"):
        assert (cd_tmp_path / name).is_file(), name
    assert "created tools.yaml" in result.output
    assert "verified: user_greeting compiles successfully (2 steps)" in result.output

    # The generated project actually compiles through the real pipeline.
    compiled = runner.invoke(app, ["compile", "workflow.yaml"])
    assert compiled.exit_code == 0
    assert "user_greeting: compiled successfully" in compiled.output


def test_init_refuses_to_overwrite(cd_tmp_path: Path) -> None:
    (cd_tmp_path / "tools.yaml").write_text("existing\n", encoding="utf-8")
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 2
    assert "refusing to overwrite" in result.output
    assert "tools.yaml" in result.output
    assert (cd_tmp_path / "tools.yaml").read_text(encoding="utf-8") == "existing\n"
    assert not (cd_tmp_path / "workflow.yaml").exists()


# --- main() exit codes (real subprocess) ----------------------------


def test_main_version_exit_zero() -> None:
    process = _run(["version"])
    assert process.returncode == 0
    assert f"FlowSpec {flowspec.__version__}" in process.stdout


def test_main_compile_valid_exit_zero(invoice_project: Path) -> None:
    process = _run(["compile", str(invoice_project / "workflow.yaml")])
    assert process.returncode == 0
    assert "compiled successfully" in process.stdout


def test_main_compile_invalid_exit_one(invoice_project: Path) -> None:
    process = _run(["compile", str(invoice_project / "workflow_invalid.yaml")])
    assert process.returncode == 1


def test_main_missing_file_exit_two(tmp_path: Path) -> None:
    process = _run(["compile", str(tmp_path / "missing.yaml")])
    assert process.returncode == 2


@pytest.mark.parametrize(
    "argv",
    [
        ["compile", "--format", "yaml", "workflow.yaml"],
        ["compile", "--bogus", "workflow.yaml"],
        ["compile"],
        ["frobnicate"],
        [],
    ],
)
def test_main_usage_errors_exit_five(argv: list[str]) -> None:
    process = _run(argv)
    assert process.returncode == 5
