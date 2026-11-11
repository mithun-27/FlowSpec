"""Base AST node definitions for FlowSpec workflows.

Nodes are immutable frozen dataclasses that preserve source locations and
never store execution state. Syntax and semantic annotations are kept
separate: nodes describe what the workflow *says*, later passes attach what
it *means*.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ASTNode", "SourceLocation"]


@dataclass(frozen=True)
class SourceLocation:
    """A position in a source file.

    ``line`` and ``column`` are 1-based; ``0`` means unknown.
    """

    file: str
    line: int = 0
    column: int = 0

    @classmethod
    def unknown(cls, file: str) -> SourceLocation:
        """A location that is known to be in ``file`` but at no known position."""
        return cls(file=file, line=0, column=0)

    def __str__(self) -> str:
        if self.line:
            return f"{self.file}:{self.line}:{self.column}"
        return self.file


@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes.

    Every concrete node is a frozen dataclass that inherits ``location`` as
    its first field. Nodes compare by value *including* location: the same
    expression written twice is two distinct nodes.
    """

    location: SourceLocation
