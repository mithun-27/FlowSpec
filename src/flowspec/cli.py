"""FlowSpec command-line interface.

Built with Typer. The CLI is the only part of FlowSpec that is allowed to
depend on terminal formatting libraries; the core compiler stays independent
of them.

Stable exit codes (specification §21):

===== ================================================
Code  Meaning
===== ================================================
0     Compilation successful
1     Compilation errors
2     Syntax or configuration error
3     Integration error
4     Internal compiler error
5     Invalid CLI usage
===== ================================================

Status: only ``flowspec version`` is implemented. Every other command reports
that it is not implemented yet and exits with code 4 (the closest stable code
for an internal unimplemented feature). See ``docs/PROGRESS.md``.
"""

from pathlib import Path
from typing import Annotated

import typer

from flowspec import __version__

app = typer.Typer(
    name="flowspec",
    help="Compile and validate AI agent tool workflows.",
    no_args_is_help=True,
    add_completion=False,
)

_NOT_IMPLEMENTED = (
    "The '{command}' command is planned but not implemented yet. "
    "See docs/PROGRESS.md for the implementation roadmap."
)
_NOT_IMPLEMENTED_EXIT_CODE = 4


def _not_implemented(command: str) -> None:
    """Report an unimplemented command and exit with a stable exit code."""
    typer.secho(_NOT_IMPLEMENTED.format(command=command), fg=typer.colors.RED, err=True)
    raise typer.Exit(_NOT_IMPLEMENTED_EXIT_CODE)


@app.command()
def version() -> None:
    """Print the FlowSpec version."""
    typer.echo(f"FlowSpec {__version__}")


@app.command()
def init() -> None:
    """Initialize a new FlowSpec project."""
    _not_implemented("init")


@app.command()
def inspect(
    tools: Annotated[Path, typer.Argument(help="Path to the tool registry file.")],
) -> None:
    """Inspect the tools declared in a registry file."""
    _not_implemented("inspect")


@app.command()
def parse(
    workflow: Annotated[Path, typer.Argument(help="Path to the workflow file.")],
) -> None:
    """Parse a workflow and display AST information."""
    _not_implemented("parse")


@app.command()
def compile(
    workflow: Annotated[Path, typer.Argument(help="Path to the workflow file.")],
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Display compiler passes and analysis results.")
    ] = False,
    emit_ir: Annotated[
        Path | None,
        typer.Option("--emit-ir", help="Write the compiled IR to this file."),
    ] = None,
    format: Annotated[
        str, typer.Option("--format", help="Output format: 'text' or 'json'.")
    ] = "text",
) -> None:
    """Compile a workflow through the complete pipeline."""
    _not_implemented("compile")


@app.command()
def explain(
    workflow: Annotated[Path, typer.Argument(help="Path to the workflow file.")],
) -> None:
    """Show dependency relationships and parameter origins."""
    _not_implemented("explain")


@app.command()
def graph(
    workflow: Annotated[Path, typer.Argument(help="Path to the workflow file.")],
    output: Annotated[
        Path | None, typer.Option("--output", help="Write the rendered graph to this file.")
    ] = None,
) -> None:
    """Generate a workflow dependency visualization."""
    _not_implemented("graph")


@app.command()
def export(
    workflow: Annotated[Path, typer.Argument(help="Path to the workflow file.")],
) -> None:
    """Export the compiled intermediate representation."""
    _not_implemented("export")


@app.command(name="test")
def test_workflows() -> None:
    """Run static workflow test suites."""
    _not_implemented("test")


@app.command(name="validate-mcp")
def validate_mcp() -> None:
    """Validate schemas imported from an MCP server."""
    _not_implemented("validate-mcp")


@app.command(name="validate-openapi")
def validate_openapi(
    spec: Annotated[Path, typer.Argument(help="Path to the OpenAPI specification.")],
) -> None:
    """Validate an OpenAPI specification."""
    _not_implemented("validate-openapi")


def main() -> None:
    """Entry point for the ``flowspec`` console script."""
    app()


if __name__ == "__main__":
    main()
