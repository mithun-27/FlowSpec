"""Source file loading shared by workflows and tool registries.

Reads a workflow or tool file from disk and parses it into a located
:class:`~flowspec.parser.document.Document`, choosing the JSON parser for
``.json`` files and the safe YAML parser for everything else. Parser
safety limits come from the compiler configuration.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from pathlib import Path

from flowspec.config import CompilerConfig
from flowspec.exceptions import ConfigurationError
from flowspec.parser.document import Document
from flowspec.parser.json_parser import parse_json_document
from flowspec.parser.yaml_parser import parse_yaml_document

__all__ = ["load_document", "read_source_text"]


def read_source_text(path: Path) -> str:
    """Read a source file, mapping missing/unreadable files to exit-code-2 errors."""
    if not path.is_file():
        raise ConfigurationError(f"file not found: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"cannot read {path}: {exc}") from exc


def load_document(path: Path, config: CompilerConfig | None = None) -> Document:
    """Parse ``path`` (JSON or YAML by extension) into a located document."""
    config = config or CompilerConfig()
    text = read_source_text(path)
    file = str(path)
    if path.suffix.lower() == ".json":
        return parse_json_document(
            text,
            file=file,
            max_size=config.max_document_size,
            max_depth=config.max_nesting_depth,
        )
    return parse_yaml_document(
        text,
        file=file,
        max_size=config.max_document_size,
        max_depth=config.max_nesting_depth,
    )
