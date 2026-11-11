"""Tests for the diagnostic model, error code registry, and formatter."""

from __future__ import annotations

from flowspec.ast.nodes import SourceLocation
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.diagnostics.formatter import format_diagnostic, format_diagnostics, format_summary
from flowspec.diagnostics.models import (
    Diagnostic,
    DiagnosticCollection,
    Severity,
    dedupe_diagnostics,
    sort_diagnostics,
)


def test_registry_contains_all_documented_codes() -> None:
    """The registry covers exactly the 22 documented codes."""
    codes = ErrorCodes.all_codes()
    assert len(codes) == 22
    assert codes[0] == "E001"
    assert codes[-1] == "E701"
    assert "E304" in codes and "E202" in codes


def test_registry_lookups() -> None:
    assert ErrorCodes.category("E202") == "type"
    assert ErrorCodes.description("E301") == "Circular dependency"
    assert ErrorCodes.is_valid("E001")
    assert not ErrorCodes.is_valid("E999")
    assert ErrorCodes.category("E999") == ""


def test_diagnostic_is_frozen_and_hashable() -> None:
    diagnostic = Diagnostic(
        code="E201",
        severity=Severity.ERROR,
        message="boom",
        location=SourceLocation(file="w.yaml", line=3, column=1),
    )
    assert diagnostic.category == "type"
    assert diagnostic.is_error
    assert hash(diagnostic) == hash(
        Diagnostic(
            code="E201",
            severity=Severity.ERROR,
            message="boom",
            location=SourceLocation(file="w.yaml", line=3, column=1),
        )
    )


def test_collection_dedupes_and_counts() -> None:
    collection = DiagnosticCollection()
    first = Diagnostic(code="E201", severity=Severity.ERROR, message="m")
    collection.add(first)
    collection.add(first)
    collection.add(Diagnostic(code="E204", severity=Severity.WARNING, message="n"))
    assert len(collection.diagnostics) == 2
    assert collection.has_errors
    assert collection.error_count == 1
    assert collection.warning_count == 1


def test_sorting_is_deterministic() -> None:
    a = Diagnostic(
        code="E202",
        severity=Severity.ERROR,
        message="b",
        location=SourceLocation(file="w.yaml", line=10),
    )
    b = Diagnostic(
        code="E202",
        severity=Severity.ERROR,
        message="b",
        location=SourceLocation(file="w.yaml", line=2),
    )
    c = Diagnostic(code="E101", severity=Severity.ERROR, message="a")
    assert sort_diagnostics([a, b, c]) == [c, b, a]
    assert dedupe_diagnostics([a, a, b]) == [a, b]


def test_formatter_renders_expected_pieces() -> None:
    diagnostic = Diagnostic(
        code="E202",
        severity=Severity.ERROR,
        message="nominal type mismatch",
        workflow="invoice_processing",
        step="send",
        location=SourceLocation(file="workflow.yaml", line=12, column=5),
        expected="InvoiceID",
        received="CustomerID",
        suggestions=("use $invoice.invoice_id",),
    )
    rendered = format_diagnostic(diagnostic)
    assert "E202" in rendered
    assert "workflow.yaml:12:5" in rendered
    assert "(invoice_processing.send)" in rendered
    assert "expected InvoiceID, received CustomerID" in rendered
    assert "suggestion: use $invoice.invoice_id" in rendered


def test_format_summary_counts() -> None:
    diagnostics = [
        Diagnostic(code="E201", severity=Severity.ERROR, message="a"),
        Diagnostic(code="E202", severity=Severity.ERROR, message="b"),
        Diagnostic(code="E204", severity=Severity.WARNING, message="c"),
    ]
    assert format_summary(diagnostics) == "2 errors, 1 warning"
    assert format_summary([]) == "no diagnostics"
    assert format_diagnostics(diagnostics).count("\n") == 2
