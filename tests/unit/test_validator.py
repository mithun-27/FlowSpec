"""Tests for structural validation of workflow and tool documents (E002)."""

from __future__ import annotations

from pathlib import Path

from flowspec.diagnostics.models import Severity
from flowspec.parser.validator import validate_tool_document, validate_workflow_document
from flowspec.parser.yaml_parser import parse_yaml_document


def _workflow_doc(text: str):
    return parse_yaml_document(text, file="workflow.yaml")


def _errors(doc) -> list[str]:
    return [d.message for d in validate_workflow_document(doc)]


def test_valid_workflow_document_has_no_errors(invoice_example_dir: Path) -> None:
    doc = parse_yaml_document(
        (invoice_example_dir / "workflow.yaml").read_text(encoding="utf-8"),
        file=str(invoice_example_dir / "workflow.yaml"),
    )
    assert validate_workflow_document(doc) == []


def test_valid_tool_document_has_no_errors(invoice_example_dir: Path) -> None:
    doc = parse_yaml_document(
        (invoice_example_dir / "tools.yaml").read_text(encoding="utf-8"),
        file=str(invoice_example_dir / "tools.yaml"),
    )
    assert validate_tool_document(doc) == []


def test_root_must_be_a_mapping() -> None:
    errors = _errors(_workflow_doc("- just\n- a\n- list\n"))
    assert any("root must be a mapping" in message for message in errors)


def test_missing_workflow_mapping() -> None:
    errors = _errors(_workflow_doc("version: '1.0'\n"))
    assert any("'workflow' mapping" in message for message in errors)


def test_missing_name() -> None:
    errors = _errors(_workflow_doc("version: '1.0'\nworkflow:\n  steps: []\n"))
    assert any("non-empty 'name'" in message for message in errors)


def test_unsupported_version() -> None:
    errors = _errors(_workflow_doc("version: '9.9'\nworkflow:\n  name: w\n  steps: []\n"))
    assert any("unsupported schema version" in message for message in errors)


def test_missing_version() -> None:
    errors = _errors(_workflow_doc("workflow:\n  name: w\n  steps: []\n"))
    assert any("missing the required 'version'" in message for message in errors)


def test_steps_must_be_a_list() -> None:
    errors = _errors(_workflow_doc("version: '1.0'\nworkflow:\n  name: w\n  steps: {}\n"))
    assert any("'steps' as a list" in message for message in errors)


def test_step_input_must_be_scalar() -> None:
    text = (
        "version: '1.0'\nworkflow:\n  name: w\n  steps:\n"
        "    - id: a\n      tool: t\n      inputs:\n        x: [1, 2]\n"
    )
    errors = _errors(_workflow_doc(text))
    assert any("scalar expression" in message for message in errors)


def test_step_must_have_id_and_tool() -> None:
    text = "version: '1.0'\nworkflow:\n  name: w\n  steps:\n    - inputs: {}\n"
    errors = _errors(_workflow_doc(text))
    assert sum("'id'" in message for message in errors) == 1
    assert sum("'tool'" in message for message in errors) == 1


def test_workflow_input_needs_type() -> None:
    text = "version: '1.0'\nworkflow:\n  name: w\n  steps: []\n  inputs:\n    email: {}\n"
    errors = _errors(_workflow_doc(text))
    assert any("non-empty 'type'" in message for message in errors)


def test_diagnostics_are_errors_with_e002() -> None:
    errors = validate_workflow_document(_workflow_doc("version: '1.0'\n"))
    assert errors
    assert all(d.code == "E002" and d.severity == Severity.ERROR for d in errors)


def test_tool_document_validations() -> None:
    base = "version: '1.0'\ntools:\n  t:\n"

    doc = _tool_doc(base + "    inputs:\n      x:\n        type: string\n")
    assert validate_tool_document(doc) == []

    doc = _tool_doc(base + "    effects:\n      - teleport\n")
    messages = [d.message for d in validate_tool_document(doc)]
    assert any("unknown effect" in message for message in messages)

    doc = _tool_doc(base + "    permissions: 'not-a-list'\n")
    messages = [d.message for d in validate_tool_document(doc)]
    assert any("'permissions' must be a list" in message for message in messages)

    doc = _tool_doc(base + "    inputs:\n      x:\n        type: 123\n")
    messages = [d.message for d in validate_tool_document(doc)]
    assert any("non-empty 'type'" in message for message in messages)


def _tool_doc(text: str):
    return parse_yaml_document(text, file="tools.yaml")
