"""Tests for safe YAML parsing: limits, duplicate keys, and locations."""

from __future__ import annotations

import pytest

from flowspec.exceptions import SourceSyntaxError
from flowspec.parser.yaml_parser import parse_yaml, parse_yaml_document


def test_parses_plain_documents() -> None:
    assert parse_yaml("a: 1\nb: [1, 2]\n") == {"a": 1, "b": [1, 2]}
    assert parse_yaml("42") == 42
    assert parse_yaml("") is None


def test_rejects_duplicate_keys() -> None:
    with pytest.raises(SourceSyntaxError, match="duplicate mapping key"):
        parse_yaml("workflow:\n  name: a\n  name: b\n")


def test_rejects_invalid_yaml() -> None:
    with pytest.raises(SourceSyntaxError, match="invalid YAML"):
        parse_yaml("workflow: [unclosed")


def test_reports_error_position() -> None:
    with pytest.raises(SourceSyntaxError) as excinfo:
        parse_yaml("a: b\nc: [x\n", file="bad.yaml")
    location = excinfo.value.location
    assert location is not None and location.file == "bad.yaml"
    assert location.line >= 2


def test_rejects_documents_over_the_size_limit() -> None:
    with pytest.raises(SourceSyntaxError, match="maximum size"):
        parse_yaml("a: 1", max_size=2)


def test_rejects_documents_over_the_depth_limit() -> None:
    nested = "a: " + "[" * 50 + "]" * 50
    with pytest.raises(SourceSyntaxError, match="maximum depth"):
        parse_yaml_document(nested, max_depth=10)


def test_unsafe_yaml_is_never_constructed() -> None:
    hostile = "!!python/object/apply:os.system [echo pwned]"
    with pytest.raises(SourceSyntaxError):
        parse_yaml(hostile)


def test_document_records_locations() -> None:
    text = "workflow:\n  name: demo\n  steps:\n    - id: customer\n"
    doc = parse_yaml_document(text, file="workflow.yaml")
    assert isinstance(doc.data, dict)
    root = doc.locate(doc.data)
    assert root is not None and root.line == 1
    workflow = doc.data["workflow"]
    located = doc.locate(workflow)
    assert located is not None and located.line == 2
    steps = workflow["steps"]
    located = doc.locate(steps)
    assert located is not None and located.line == 4
    assert doc.located("not-in-the-document").file == "workflow.yaml"


def test_compose_mismatch_degrades_gracefully() -> None:
    # Merge keys and aliases are not location-tracked; parsing still succeeds.
    text = "a: &x {k: 1}\nb:\n  <<: *x\n"
    doc = parse_yaml_document(text)
    assert doc.data["b"] == {"k": 1}
