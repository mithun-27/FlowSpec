# API Reference

The FlowSpec public Python API for the v0.1.0 compiler foundation:
parse a workflow, compile it against a tool registry, and inspect the
result. Everything below is implemented and covered by the test suite.
Later milestones (MCP/OpenAPI/Python tool registration, the execution
runtime, visualization rendering) will extend this surface; see
[PROGRESS.md](PROGRESS.md).

## Usage

```python
from flowspec import Compiler, CompilerConfig

compiler = Compiler(CompilerConfig(strict_types=True))

# The tool schema defaults to the tools.yaml/tools.json next to the
# workflow file; pass tools_path to point elsewhere.
result = compiler.compile("workflow.yaml", tools_path="tools.yaml")

if result.success:
    print("Compilation successful")
    print(result.execution_order)     # ('customer', 'invoice', ...)
    print(result.ir.to_json())        # deterministic IR JSON
else:
    for diagnostic in result.diagnostics:
        print(diagnostic.message)     # structured, ordered diagnostics
```

`compile` never executes a tool and is deterministic: the same inputs
and configuration always produce the same result. Missing or unreadable
source files raise `flowspec.exceptions.ConfigurationError`; the CLI
maps that to exit code 2.

## Core objects

All importable from the package root:

| Object | Role |
| ------ | ---- |
| `Compiler` | Facade: compile a workflow project through the full pipeline |
| `CompilerConfig` | Strict typing, cycle detection, permissions, IR options; `from_file`/`from_dict` loaders |
| `CompilationPipeline` | Pass orchestration (P0-P12) behind the facade |
| `CompilationResult` | Success with IR and execution plan, or failure with diagnostics |
| `IntermediateRepresentation` | Versioned (`1.0`), deterministic compiled output; `to_dict`/`to_json` |
| `WorkflowNode` | Parsed workflow representation (AST root) |
| `ToolDefinition` | A tool's declared contract |
| `ToolRegistry` | The set of known tools |
| `Type` | FlowSpec type values (primitive, nominal, generic, union, `any`) |
| `TypeChecker` | Type compatibility checking |
| `WorkflowGraph` | Dependency graph with adjacency and reverse adjacency |
| `Diagnostic` | Structured error information (code, severity, location, suggestions) |

`CompilationResult` exposes `workflow_name`, `diagnostics`, `ir`,
`graph`, `stages`, and the `success`, `error_count`, `warning_count`,
and `execution_order` properties, plus `summary()`, `formatted()`, and
`to_dict()`.

## Exporting artifacts

```python
from flowspec import Compiler
from flowspec.visualization.exporters import export_ir, export_result

result = Compiler().compile("workflow.yaml")

export_ir(result)      # IR JSON; ValueError when result.ir is None
export_result(result)  # full outcome JSON, diagnostics included
```

Both emit deterministic JSON: sorted keys, no timestamps.

## Exit codes (CLI)

| Code | Meaning |
| ---- | ------- |
| 0 | Compilation successful |
| 1 | Compilation errors |
| 2 | Syntax or configuration error |
| 3 | Integration error |
| 4 | Internal compiler error |
| 5 | Invalid CLI usage |

Implemented commands: `version`, `init`, `inspect`, `parse`, `compile`,
`explain`, `export`. `test`, `graph`, `validate-mcp`, and
`validate-openapi` report that they are not implemented yet and exit
with code 4.

## Stability

The public API is versioned. Breaking changes only happen in major
releases; the workflow schema and IR carry explicit `version` fields and
are never silently broken.
