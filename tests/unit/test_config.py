"""Tests for compiler configuration loading and validation."""

from __future__ import annotations

import pytest

from flowspec.config import CompilerConfig
from flowspec.exceptions import ConfigurationError


def test_defaults() -> None:
    config = CompilerConfig()
    assert config.strict_types
    assert not config.allow_unknown_types
    assert config.detect_cycles
    assert config.generate_ir
    assert config.max_document_size == 1_000_000
    assert config.max_nesting_depth == 100


def test_from_dict_overrides() -> None:
    config = CompilerConfig.from_dict({"strict_types": False, "generate_ir": False})
    assert not config.strict_types
    assert not config.generate_ir
    assert config.detect_cycles  # untouched default


def test_unknown_keys_are_rejected() -> None:
    with pytest.raises(ConfigurationError, match="unknown compiler configuration"):
        CompilerConfig.from_dict({"frobnicate": True})


def test_wrong_value_types_are_rejected() -> None:
    with pytest.raises(ConfigurationError, match="must be"):
        CompilerConfig.from_dict({"strict_types": "yes"})


def test_limits_must_be_positive() -> None:
    with pytest.raises(ConfigurationError, match="positive"):
        CompilerConfig.from_dict({"max_nesting_depth": 0})


def test_from_project_dict() -> None:
    config = CompilerConfig.from_project_dict(
        {"project": {"name": "demo"}, "compiler": {"strict_types": False}}
    )
    assert not config.strict_types


def test_from_file(tmp_path) -> None:
    project = tmp_path / "flowspec.yaml"
    project.write_text(
        "version: '1.0'\nproject:\n  name: demo\ncompiler:\n  allow_unknown_types: true\n",
        encoding="utf-8",
    )
    config = CompilerConfig.from_file(project)
    assert config.allow_unknown_types

    with pytest.raises(ConfigurationError, match="not found"):
        CompilerConfig.from_file(tmp_path / "missing.yaml")
