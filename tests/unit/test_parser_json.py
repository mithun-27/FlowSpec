"""Tests for safe JSON parsing: limits, duplicate keys, and error positions."""

from __future__ import annotations

import pytest

from flowspec.exceptions import SourceSyntaxError
from flowspec.parser.json_parser import parse_json, parse_json_document


def test_parses_plain_documents() -> None:
    assert parse_json('{"a": 1, "b": [1, 2]}') == {"a": 1, "b": [1, 2]}
    assert parse_json("42") == 42
    assert parse_json("null") is None


def test_rejects_duplicate_keys() -> None:
    with pytest.raises(SourceSyntaxError, match="duplicate object key"):
        parse_json('{"workflow": {"name": "a", "name": "b"}}')


def test_rejects_invalid_json_with_position() -> None:
    with pytest.raises(SourceSyntaxError) as excinfo:
        parse_json('{"a": 1,\n  "b": truncated}', file="bad.json")
    assert excinfo.value.location is not None
    assert excinfo.value.location.file == "bad.json"
    assert excinfo.value.location.line == 2


def test_rejects_documents_over_the_size_limit() -> None:
    with pytest.raises(SourceSyntaxError, match="maximum size"):
        parse_json('{"a": 1}', max_size=4)


def test_rejects_documents_over_the_depth_limit() -> None:
    nested = "[" * 50 + "]" * 50
    with pytest.raises(SourceSyntaxError, match="maximum depth"):
        parse_json_document(nested, max_depth=10)


def test_documents_carry_no_value_locations_yet() -> None:
    doc = parse_json_document('{"workflow": {"name": "demo"}}')
    assert doc.format == "json"
    assert doc.locate(doc.data["workflow"]) is None
