"""The FlowSpec compiler facade.

``Compiler`` is the main public entry point: given a workflow file (and
optionally its tool schema), it runs the full pass pipeline and returns
a :class:`~flowspec.compiler.result.CompilationResult` — the versioned
intermediate representation with its dependency-aware execution plan
for a valid workflow, or aggregated structured diagnostics for an
invalid one. Invalid workflows never produce executable IR.

The tool schema defaults to the ``tools.yaml`` (or ``tools.json``)
sitting next to the workflow file; pass ``tools_path`` to point
elsewhere. Missing or unreadable files raise
:class:`~flowspec.exceptions.ConfigurationError`.

Compilation is deterministic and never executes a tool.

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from pathlib import Path

from flowspec.compiler.pipeline import CompilationPipeline
from flowspec.compiler.result import CompilationResult
from flowspec.config import CompilerConfig

__all__ = ["Compiler"]


class Compiler:
    """The public FlowSpec compiler."""

    def __init__(self, config: CompilerConfig | None = None) -> None:
        self.config = config or CompilerConfig()

    def compile(
        self,
        workflow_path: str | Path,
        tools_path: str | Path | None = None,
    ) -> CompilationResult:
        """Compile one workflow project.

        Args:
            workflow_path: the workflow file (YAML or JSON).
            tools_path: the tool schema file; when omitted, the sibling
                ``tools.yaml``/``tools.json`` next to the workflow is used.

        Returns:
            The compilation result: IR and execution plan on success,
            structured diagnostics on failure.

        Raises:
            ConfigurationError: a source file is missing or unreadable
                (CLI exit code 2).
        """
        return CompilationPipeline(self.config).run(workflow_path, tools_path)
