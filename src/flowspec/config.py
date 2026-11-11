"""Compiler configuration for FlowSpec.

``CompilerConfig`` carries the settings declared in a project's
``flowspec.yaml``: strict typing, unknown-type policy, cycle detection,
permission validation, IR generation, and parser safety limits. Unknown
configuration keys are rejected rather than silently ignored.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from flowspec.exceptions import ConfigurationError

__all__ = ["CompilerConfig"]

_DEFAULT_COMPILER_SECTION: dict[str, Any] = {
    "strict_types": True,
    "allow_unknown_types": False,
    "detect_cycles": True,
    "validate_permissions": True,
    "generate_ir": True,
    "max_document_size": 1_000_000,
    "max_nesting_depth": 100,
}


@dataclass(frozen=True)
class CompilerConfig:
    """Validated configuration for the compiler pipeline.

    Attributes:
        strict_types: reject ``any`` involvement and narrowing conversions
            such as ``float`` → ``integer`` unless explicitly allowed.
        allow_unknown_types: accept nominal types that no tool contract
            declares (otherwise E203 in strict mode).
        detect_cycles: run circular-dependency detection (E301).
        validate_permissions: check declared permissions (metadata only).
        generate_ir: emit executable IR for valid workflows.
        max_document_size: maximum accepted document size, in characters.
        max_nesting_depth: maximum accepted YAML/JSON nesting depth.
    """

    strict_types: bool = True
    allow_unknown_types: bool = False
    detect_cycles: bool = True
    validate_permissions: bool = True
    generate_ir: bool = True
    max_document_size: int = 1_000_000
    max_nesting_depth: int = 100

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CompilerConfig:
        """Build a config from a ``compiler``-section mapping.

        Raises :class:`ConfigurationError` for unknown keys or values of
        the wrong type — invalid configuration is never silently ignored.
        """
        unknown = set(data) - set(_DEFAULT_COMPILER_SECTION)
        if unknown:
            raise ConfigurationError(
                f"unknown compiler configuration keys: {', '.join(sorted(unknown))}"
            )

        values: dict[str, Any] = {}
        for key, default in _DEFAULT_COMPILER_SECTION.items():
            if key not in data:
                values[key] = default
                continue
            value = data[key]
            if not isinstance(value, type(default)):
                raise ConfigurationError(
                    f"compiler configuration '{key}' must be "
                    f"{type(default).__name__}, received {type(value).__name__}"
                )
            values[key] = value

        config = cls(**values)
        if config.max_document_size <= 0 or config.max_nesting_depth <= 0:
            raise ConfigurationError("max_document_size and max_nesting_depth must be positive")
        return config

    @classmethod
    def from_project_dict(cls, data: Mapping[str, Any]) -> CompilerConfig:
        """Build a config from a full ``flowspec.yaml`` document."""
        section = data.get("compiler", {})
        if not isinstance(section, Mapping):
            raise ConfigurationError("'compiler' section must be a mapping")
        return cls.from_dict(section)

    @classmethod
    def from_file(cls, path: str | Path) -> CompilerConfig:
        """Load a config from a ``flowspec.yaml`` project file."""
        file = Path(path)
        if not file.is_file():
            raise ConfigurationError(f"configuration file not found: {file}")
        try:
            data = yaml.safe_load(file.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"invalid configuration file {file}: {exc}") from exc
        if not isinstance(data, Mapping):
            raise ConfigurationError(f"configuration file {file} must be a mapping")
        return cls.from_project_dict(data)
