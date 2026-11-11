"""Tests for the compilation result object."""

from __future__ import annotations

from flowspec.compiler.ir import IntermediateRepresentation
from flowspec.compiler.result import CompilationResult
from flowspec.diagnostics.models import Diagnostic, Severity


def _diag(code: str = "E101", severity: str = Severity.ERROR) -> Diagnostic:
    return Diagnostic(code=code, severity=severity, message="a problem")


def _ir() -> IntermediateRepresentation:
    return IntermediateRepresentation(
        workflow_name="w",
        description=None,
        schema_version="1.0",
        inputs=(),
        outputs=(),
        steps=(),
        order=("a", "b"),
        stages=(("a",), ("b",)),
        graph={},
        effects=(),
        permissions=(),
    )


def test_success_with_no_diagnostics() -> None:
    result = CompilationResult(workflow_name="w", diagnostics=())

    assert result.success
    assert not result.has_errors
    assert result.error_count == 0
    assert result.warning_count == 0
    assert result.ir is None
    assert result.execution_order == ()


def test_errors_block_success() -> None:
    result = CompilationResult(
        workflow_name="w",
        diagnostics=(_diag("E101"), _diag("E202")),
    )

    assert not result.success
    assert result.has_errors
    assert result.error_count == 2
    assert result.warning_count == 0
    assert result.summary() == "2 errors"
    assert result.formatted().count("\n") == 1  # one line per diagnostic


def test_warnings_do_not_block_success() -> None:
    result = CompilationResult(
        workflow_name="w",
        diagnostics=(_diag("E303", Severity.WARNING),),
    )

    assert result.success
    assert not result.has_errors
    assert result.warning_count == 1
    assert result.summary() == "1 warning"


def test_mixed_severity_counts() -> None:
    result = CompilationResult(
        workflow_name="w",
        diagnostics=(
            _diag("E101"),
            _diag("E202"),
            _diag("E303", Severity.WARNING),
            _diag("E303", Severity.WARNING),
            _diag("E303", Severity.WARNING),
        ),
    )

    assert not result.success
    assert result.error_count == 2
    assert result.warning_count == 3
    assert result.summary() == "2 errors, 3 warnings"


def test_execution_order_comes_from_the_ir() -> None:
    result = CompilationResult(workflow_name="w", diagnostics=(), ir=_ir())

    assert result.success
    assert result.execution_order == ("a", "b")


def test_to_dict_without_ir() -> None:
    result = CompilationResult(
        workflow_name="w",
        diagnostics=(_diag(),),
    )

    as_dict = result.to_dict()

    assert as_dict["success"] is False
    assert as_dict["workflow"] == "w"
    assert as_dict["summary"] == "1 error"
    assert as_dict["ir"] is None
    assert len(as_dict["diagnostics"]) == 1
    assert as_dict["diagnostics"][0]["code"] == "E101"


def test_to_dict_with_ir() -> None:
    ir = _ir()
    result = CompilationResult(workflow_name="w", diagnostics=(), ir=ir)

    as_dict = result.to_dict()

    assert as_dict["success"] is True
    assert as_dict["ir"] == ir.to_dict()
    assert as_dict["ir"]["execution"]["order"] == ["a", "b"]


def test_formatted_renders_every_diagnostic() -> None:
    result = CompilationResult(
        workflow_name="w",
        diagnostics=(
            _diag("E101"),
            _diag("E303", Severity.WARNING),
        ),
    )

    lines = result.formatted().splitlines()

    assert len(lines) == 2
    assert lines[0].startswith("E101")
    assert lines[1].startswith("E303")
