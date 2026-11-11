"""FlowSpec command-line interface.

Built with Typer. The CLI is the only part of FlowSpec that is allowed to
depend on terminal formatting libraries; the core compiler stays independent
of them. All regular output is plain ASCII text, safe for every console
encoding.

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

Commands implemented for the v0.1.0 compiler foundation: ``version``,
``init``, ``inspect``, ``parse``, ``compile``, ``explain``, and ``export``.
``graph`` (v0.4.0), ``test``, ``validate-mcp`` (v0.3.0), and
``validate-openapi`` (v0.3.0) are not implemented yet; they report that
honestly and exit with code 4. See ``docs/PROGRESS.md``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn

import typer
from typer.exceptions import TyperException

from flowspec import __version__
from flowspec.ast.expressions import describe_expression
from flowspec.compiler.compiler import Compiler
from flowspec.compiler.pipeline import PIPELINE_PASSES
from flowspec.compiler.result import CompilationResult
from flowspec.config import CompilerConfig
from flowspec.diagnostics.formatter import format_diagnostic
from flowspec.diagnostics.models import Diagnostic
from flowspec.exceptions import ConfigurationError, SourceError
from flowspec.parser.ast_builder import build_workflow_ast
from flowspec.parser.loader import load_document
from flowspec.parser.validator import validate_workflow_document
from flowspec.registry.schema_loader import load_tool_schema
from flowspec.registry.tool_registry import ParameterSpec
from flowspec.visualization.exporters import export_ir, export_result

app = typer.Typer(
    name="flowspec",
    help="Compile and validate AI agent tool workflows.",
    no_args_is_help=True,
    add_completion=False,
)

EXIT_SUCCESS = 0
EXIT_COMPILE_ERRORS = 1
EXIT_CONFIGURATION = 2
EXIT_INTERNAL = 4
EXIT_USAGE = 5

OUTPUT_FORMATS = ("text", "json")

_NOT_IMPLEMENTED = (
    "The '{command}' command is planned but not implemented yet. "
    "See docs/PROGRESS.md for the implementation roadmap."
)

#: Project configuration file looked up next to each source file.
_PROJECT_CONFIG = "flowspec.yaml"

_INIT_FLOWSPEC_YAML = """\
compiler:
  strict_types: true
  allow_unknown_types: false
  detect_cycles: true
  validate_permissions: true
  generate_ir: true
"""

_INIT_TOOLS_YAML = """\
version: '1.0'

tools:

  fetch_user:
    description: Look up a user by email.
    inputs:
      email:
        type: string
        required: true
    outputs:
      user_id:
        type: UserID
      display_name:
        type: string
    effects:
      - read
    permissions:
      - users.read

  notify_user:
    description: Send a notification to a user.
    inputs:
      user_id:
        type: UserID
        required: true
      message:
        type: string
        required: true
    outputs:
      sent:
        type: boolean
    effects:
      - external_write
    permissions:
      - users.notify
"""

_INIT_WORKFLOW_YAML = """\
version: '1.0'

workflow:
  name: user_greeting
  description: Look up a user and send them a greeting.

  inputs:
    email:
      type: string
      required: true
    message:
      type: string
      required: true

  steps:
    - id: user
      tool: fetch_user
      inputs:
        email: $input.email

    - id: notify
      tool: notify_user
      inputs:
        user_id: $user.user_id
        message: $input.message

  outputs:
    sent: $notify.sent
"""


def _error(message: str) -> None:
    """Print an error line to stderr."""
    typer.secho(message, fg=typer.colors.RED, err=True)


def _not_implemented(command: str) -> None:
    """Report an unimplemented command and exit with a stable exit code."""
    _error(_NOT_IMPLEMENTED.format(command=command))
    raise typer.Exit(EXIT_INTERNAL)


def _load_config(source: Path) -> CompilerConfig:
    """The project configuration: ``flowspec.yaml`` beside the source file.

    Projects without a configuration file use the defaults; invalid
    project configuration raises :class:`ConfigurationError` (exit 2).
    """
    project_file = source.parent / _PROJECT_CONFIG
    if project_file.is_file():
        return CompilerConfig.from_file(project_file)
    return CompilerConfig()


def _configuration_error(exc: ConfigurationError) -> NoReturn:
    """Report a configuration problem and exit with code 2."""
    _error(f"configuration error: {exc}")
    raise typer.Exit(EXIT_CONFIGURATION) from exc


def _source_error(exc: SourceError) -> NoReturn:
    """Report a workflow source error as a diagnostic and exit with code 1."""
    location = f"{exc.location} " if exc.location else ""
    typer.secho(f"{exc.code} {location}{exc.message}", err=True)
    raise typer.Exit(EXIT_COMPILE_ERRORS) from exc


def _compile(workflow: Path, tools: Path | None) -> CompilationResult:
    """Compile a workflow with its project configuration (exit 2 on config errors)."""
    try:
        config = _load_config(workflow)
        return Compiler(config).compile(workflow, tools)
    except ConfigurationError as exc:
        _configuration_error(exc)


def _print_diagnostics(diagnostics: list[Diagnostic] | tuple[Diagnostic, ...]) -> None:
    """Print diagnostics, one per line, to stderr."""
    for diagnostic in diagnostics:
        typer.secho(format_diagnostic(diagnostic), err=True)


def _print_passes() -> None:
    """Print the pipeline pass table and its implementation status."""
    typer.echo("compiler passes:")
    for code, name, status in PIPELINE_PASSES:
        typer.echo(f"  {code} {name} [{status}]")


def _report(result: CompilationResult, *, verbose: bool = False) -> None:
    """Print a compilation result as text."""
    if verbose:
        _print_passes()
    name = result.workflow_name or "<unknown>"
    if result.success:
        typer.echo(f"{name}: compiled successfully")
        if result.ir is not None:
            typer.echo(f"steps: {len(result.ir.steps)}")
        if result.execution_order:
            typer.echo(f"execution order: {' -> '.join(result.execution_order)}")
        if result.stages:
            typer.echo(
                "execution stages: " + ", ".join("/".join(stage.steps) for stage in result.stages)
            )
        if verbose and result.ir is not None:
            typer.echo(f"effects: {', '.join(result.ir.effects) or '-'}")
            typer.echo(f"permissions: {', '.join(result.ir.permissions) or '-'}")
    else:
        _error(f"{name}: {result.summary()}")
        _print_diagnostics(result.diagnostics)


def _write_ir(result: CompilationResult, destination: Path) -> None:
    """Write a compiled IR to a file (deterministic JSON)."""
    if result.ir is None:
        _error("no IR to write: the workflow did not compile cleanly")
        return
    try:
        destination.write_text(export_ir(result) + "\n", encoding="utf-8")
    except OSError as exc:
        _error(f"cannot write {destination}: {exc}")
        raise typer.Exit(EXIT_CONFIGURATION) from exc
    typer.echo(f"wrote IR to {destination}")


def _require_format(format: str) -> None:
    """Reject output formats that do not exist (exit code 5)."""
    if format not in OUTPUT_FORMATS:
        _error(f"invalid --format '{format}': expected one of {', '.join(OUTPUT_FORMATS)}")
        raise typer.Exit(EXIT_USAGE)


def _input_flags(parameter: ParameterSpec) -> str:
    """Required/nullable input flags rendered for display."""
    parts = ["required" if parameter.required else "optional"]
    if parameter.nullable:
        parts.append("nullable")
    return f" ({', '.join(parts)})"


def _output_flags(parameter: ParameterSpec) -> str:
    """Nullable output flag rendered for display."""
    return " (nullable)" if parameter.nullable else ""


@app.command()
def version() -> None:
    """Print the FlowSpec version."""
    typer.echo(f"FlowSpec {__version__}")


@app.command()
def init() -> None:
    """Initialize a new FlowSpec project in the current directory."""
    targets = {
        "flowspec.yaml": _INIT_FLOWSPEC_YAML,
        "tools.yaml": _INIT_TOOLS_YAML,
        "workflow.yaml": _INIT_WORKFLOW_YAML,
    }
    existing = [name for name in targets if Path(name).exists()]
    if existing:
        _error(f"refusing to overwrite existing file(s): {', '.join(sorted(existing))}")
        raise typer.Exit(EXIT_CONFIGURATION)
    try:
        for name, content in targets.items():
            Path(name).write_text(content, encoding="utf-8")
            typer.echo(f"created {name}")
    except OSError as exc:
        _error(f"cannot write project files: {exc}")
        raise typer.Exit(EXIT_CONFIGURATION) from exc

    # init never ships a broken project: verify the scaffold compiles.
    result = _compile(Path("workflow.yaml"), None)
    if not result.success:
        _error("the generated project does not compile; this is a FlowSpec bug")
        raise typer.Exit(EXIT_INTERNAL)
    name = result.workflow_name or "workflow"
    typer.echo(f"verified: {name} compiles successfully ({len(result.execution_order)} steps)")


@app.command()
def inspect(
    tools: Annotated[Path, typer.Argument(help="Path to the tool registry file.")],
) -> None:
    """Inspect the tools declared in a registry file."""
    try:
        config = _load_config(tools)
        registry, diagnostics = load_tool_schema(tools, config)
    except ConfigurationError as exc:
        _configuration_error(exc)
    except SourceError as exc:
        _source_error(exc)
    if diagnostics:
        _print_diagnostics(diagnostics)
    if any(diagnostic.is_error for diagnostic in diagnostics):
        raise typer.Exit(EXIT_COMPILE_ERRORS)

    typer.echo(f"{len(registry)} tool(s)")
    for tool in registry:
        typer.echo(f"{tool.name}: {tool.description or '(no description)'}")
        for parameter in tool.inputs:
            typer.echo(
                f"  input  {parameter.name}: {parameter.type.render()}{_input_flags(parameter)}"
            )
        for parameter in tool.outputs:
            typer.echo(
                f"  output {parameter.name}: {parameter.type.render()}{_output_flags(parameter)}"
            )
        typer.echo(f"  effects: {', '.join(tool.effects) or '-'}")
        typer.echo(f"  permissions: {', '.join(tool.permissions) or '-'}")


@app.command()
def parse(
    workflow: Annotated[Path, typer.Argument(help="Path to the workflow file.")],
) -> None:
    """Parse a workflow and display AST information."""
    try:
        config = _load_config(workflow)
        document = load_document(workflow, config)
    except ConfigurationError as exc:
        _configuration_error(exc)
    except SourceError as exc:
        _source_error(exc)

    diagnostics = validate_workflow_document(document)
    if diagnostics:
        _print_diagnostics(diagnostics)
    if any(diagnostic.is_error for diagnostic in diagnostics):
        raise typer.Exit(EXIT_COMPILE_ERRORS)

    try:
        workflow_ast = build_workflow_ast(document)
    except SourceError as exc:
        _source_error(exc)

    typer.echo(f"workflow: {workflow_ast.name}")
    if workflow_ast.description:
        typer.echo(f"description: {workflow_ast.description}")
    if workflow_ast.inputs:
        typer.echo("inputs:")
        for name, input_node in workflow_ast.inputs.items():
            required = "required" if input_node.required else "optional"
            typer.echo(f"  {name}: {input_node.type_name} ({required})")
    typer.echo(f"steps ({len(workflow_ast.steps)}):")
    for step in workflow_ast.steps:
        typer.echo(f"  {step.id} [{step.tool}]")
        for argument, expression in step.inputs.items():
            typer.echo(f"    {argument} <- {describe_expression(expression)}")
    if workflow_ast.outputs:
        typer.echo("outputs:")
        for name, output_node in workflow_ast.outputs.items():
            typer.echo(f"  {name} <- {describe_expression(output_node.expression)}")


@app.command()
def compile(
    workflow: Annotated[Path, typer.Argument(help="Path to the workflow file.")],
    tools: Annotated[
        Path | None,
        typer.Option("--tools", help="Path to the tool registry file."),
    ] = None,
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
    _require_format(format)
    result = _compile(workflow, tools)
    if format == "json":
        typer.echo(export_result(result))
    else:
        _report(result, verbose=verbose)
    if emit_ir is not None:
        _write_ir(result, emit_ir)
    raise typer.Exit(EXIT_SUCCESS if result.success else EXIT_COMPILE_ERRORS)


@app.command()
def explain(
    workflow: Annotated[Path, typer.Argument(help="Path to the workflow file.")],
    tools: Annotated[
        Path | None,
        typer.Option("--tools", help="Path to the tool registry file."),
    ] = None,
) -> None:
    """Show dependency relationships and parameter origins."""
    result = _compile(workflow, tools)
    if result.ir is None:
        _report(result)
        _error("explain requires a workflow that compiles cleanly")
        raise typer.Exit(EXIT_COMPILE_ERRORS)

    typer.echo(f"workflow: {result.workflow_name}")
    typer.echo("steps:")
    for step in result.ir.steps:
        typer.echo(f"  {step.position}. {step.id} [{step.tool}]")
        typer.echo(f"     depends on: {', '.join(step.dependencies) or '-'}")
        for argument in step.inputs:
            typer.echo(f"     {argument.argument} <- {argument.source} : {argument.type}")
        for output in step.outputs:
            nullable = " (nullable)" if output.nullable else ""
            typer.echo(f"     outputs {output.name} : {output.type}{nullable}")
    typer.echo("workflow outputs:")
    for binding in result.ir.outputs:
        typer.echo(f"  {binding.name} <- {binding.source} : {binding.type}")
    typer.echo("execution stages:")
    for index, stage in enumerate(result.ir.stages, start=1):
        typer.echo(f"  {index}. {', '.join(stage)}")


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
    tools: Annotated[
        Path | None,
        typer.Option("--tools", help="Path to the tool registry file."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Write the IR to this file instead of stdout."),
    ] = None,
) -> None:
    """Export the compiled intermediate representation."""
    result = _compile(workflow, tools)
    if result.ir is None:
        _report(result)
        _error("no IR to export: the workflow did not compile cleanly")
        raise typer.Exit(EXIT_COMPILE_ERRORS)
    if output is None:
        typer.echo(export_ir(result))
        raise typer.Exit(EXIT_SUCCESS)
    _write_ir(result, output)
    raise typer.Exit(EXIT_SUCCESS)


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
    """Entry point for the ``flowspec`` console script.

    Runs the app in non-standalone mode so FlowSpec owns the exit codes:
    command results keep their stable codes, and framework usage errors
    (unknown options, missing arguments) map to exit code 5 instead of
    the library default 2, which the specification reserves for syntax
    and configuration errors.
    """
    try:
        code = app(standalone_mode=False)
    except TyperException as exc:
        _error(f"usage error: {exc.format_message()}")
        raise SystemExit(EXIT_USAGE) from exc
    raise SystemExit(code if isinstance(code, int) else EXIT_SUCCESS)


if __name__ == "__main__":
    main()
