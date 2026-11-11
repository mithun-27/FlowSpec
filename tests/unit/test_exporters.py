"""Unit tests for the deterministic JSON exporters."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from flowspec.compiler.compiler import Compiler
from flowspec.config import CompilerConfig
from flowspec.visualization.exporters import export_ir, export_result


def test_export_ir_renders_the_ir_json(invoice_example_dir: Path) -> None:
    result = Compiler().compile(invoice_example_dir / "workflow.yaml")
    assert result.ir is not None
    text = export_ir(result)
    assert text == result.ir.to_json()
    parsed = json.loads(text)
    assert parsed["ir_version"] == "1.0"
    assert parsed["workflow"]["name"] == "invoice_processing"
    assert parsed["execution"]["order"] == ["customer", "invoice", "payment", "send"]


def test_export_ir_honors_indentation(invoice_example_dir: Path) -> None:
    result = Compiler().compile(invoice_example_dir / "workflow.yaml")
    assert result.ir is not None
    assert export_ir(result, indent=4) == result.ir.to_json(indent=4)
    assert '    "ir_version":' in export_ir(result, indent=4)


def test_export_ir_requires_an_ir(invoice_example_dir: Path) -> None:
    """A failed compilation never exports executable IR."""
    result = Compiler().compile(invoice_example_dir / "workflow_invalid.yaml")
    assert result.ir is None
    with pytest.raises(ValueError, match=re.escape("no IR")):
        export_ir(result)


def test_export_ir_requires_ir_generation_enabled(invoice_example_dir: Path) -> None:
    """A clean compile with IR generation disabled has nothing to export."""
    config = CompilerConfig(generate_ir=False)
    result = Compiler(config).compile(invoice_example_dir / "workflow.yaml")
    assert result.success
    assert result.ir is None
    with pytest.raises(ValueError, match=re.escape("no IR")):
        export_ir(result)


def test_export_result_round_trips_success(invoice_example_dir: Path) -> None:
    result = Compiler().compile(invoice_example_dir / "workflow.yaml")
    parsed = json.loads(export_result(result))
    assert parsed == result.to_dict()
    assert parsed["success"] is True
    assert parsed["workflow"] == "invoice_processing"
    assert parsed["summary"] == "no diagnostics"
    assert parsed["diagnostics"] == []
    assert parsed["ir"]["ir_version"] == "1.0"


def test_export_result_includes_failure_diagnostics(invoice_example_dir: Path) -> None:
    result = Compiler().compile(invoice_example_dir / "workflow_invalid.yaml")
    parsed = json.loads(export_result(result))
    assert parsed == result.to_dict()
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


def test_exports_are_deterministic(invoice_example_dir: Path) -> None:
    first = Compiler().compile(invoice_example_dir / "workflow.yaml")
    again = Compiler().compile(invoice_example_dir / "workflow.yaml")
    assert export_ir(first) == export_ir(again)
    assert export_result(first) == export_result(again)
