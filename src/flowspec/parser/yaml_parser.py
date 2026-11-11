"""Safe YAML loading for FlowSpec workflow and tool documents.

- Loads YAML with the safe loader — no arbitrary Python object
  construction is ever possible from workflow input.
- Rejects duplicate mapping keys instead of silently keeping the last one.
- Enforces document size and nesting-depth limits against hostile input.
- Records source locations for every mapping and sequence so later passes
  can attach precise positions to diagnostics.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from typing import Any

import yaml

from flowspec.ast.nodes import SourceLocation
from flowspec.exceptions import SourceSyntaxError
from flowspec.parser.document import Document, check_nesting_depth

__all__ = ["parse_yaml", "parse_yaml_document"]

DEFAULT_MAX_SIZE = 1_000_000
DEFAULT_MAX_DEPTH = 100


class _UniqueKeyLoader(yaml.SafeLoader):
    """A safe loader that rejects duplicate mapping keys.

    Merge keys (``<<: *anchor``) are resolved first, so a key repeated
    across a merge and the local mapping is also rejected.
    """

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        self.flatten_mapping(node)
        seen: set = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in seen
            except TypeError:  # unhashable key: let the base class raise
                continue
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f"duplicate mapping key {key!r}",
                    key_node.start_mark,
                )
            seen.add(key)
        result: dict = super().construct_mapping(node, deep=deep)
        return result


def _mark_location(mark: Any, file: str) -> SourceLocation:
    line = getattr(mark, "line", None)
    column = getattr(mark, "column", None)
    if line is None or column is None:
        return SourceLocation.unknown(file)
    return SourceLocation(file=file, line=line + 1, column=column + 1)


def parse_yaml(
    text: str,
    *,
    file: str = "<string>",
    max_size: int = DEFAULT_MAX_SIZE,
) -> Any:
    """Safely parse a YAML document into plain Python data.

    Raises :class:`SourceSyntaxError` (E001) for invalid YAML, duplicate
    mapping keys, or documents exceeding the size limit.
    """
    if len(text) > max_size:
        raise SourceSyntaxError(
            f"document exceeds the maximum size of {max_size} characters",
            location=SourceLocation.unknown(file),
        )
    try:
        return yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None) or getattr(exc, "context_mark", None)
        raise SourceSyntaxError(
            _yaml_error_message(exc), location=_mark_location(mark, file) if mark else None
        ) from exc


def _yaml_error_message(exc: yaml.YAMLError) -> str:
    problem = getattr(exc, "problem", None)
    if problem:
        return f"invalid YAML: {problem}"
    return f"invalid YAML: {exc}"


def _compose_locations(text: str, data: Any, file: str) -> dict[int, SourceLocation]:
    """Walk the composed node tree next to the constructed data and record
    the location of every mapping and sequence."""
    locations: dict[int, SourceLocation] = {}
    try:
        root = yaml.compose(text, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        return locations

    stack: list[tuple[Any, Any]] = [(root, data)]
    while stack:
        node, plain = stack.pop()
        if isinstance(node, yaml.MappingNode) and isinstance(plain, dict):
            locations[id(plain)] = _mark_location(node.start_mark, file)
            pairs = list(node.value)
            items = list(plain.items())
            if len(pairs) == len(items):
                for (_, value_node), (_, value_plain) in zip(pairs, items, strict=True):
                    stack.append((value_node, value_plain))
        elif isinstance(node, yaml.SequenceNode) and isinstance(plain, list):
            locations[id(plain)] = _mark_location(node.start_mark, file)
            if len(node.value) == len(plain):
                stack.extend(zip(node.value, plain, strict=True))
    return locations


def parse_yaml_document(
    text: str,
    *,
    file: str = "<string>",
    max_size: int = DEFAULT_MAX_SIZE,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> Document:
    """Parse YAML into a located :class:`Document`.

    Raises :class:`SourceSyntaxError` (E001) for invalid YAML, duplicate
    keys, or size/depth limit violations.
    """
    data = parse_yaml(text, file=file, max_size=max_size)
    check_nesting_depth(data, max_depth=max_depth, file=file)
    locations = _compose_locations(text, data, file)
    return Document(data=data, file=file, locations=locations, format="yaml")
