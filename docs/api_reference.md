# API Reference

> **Design document — implementation pending.** This document describes
> the planned public Python API of FlowSpec. See [PROGRESS.md](PROGRESS.md)
> for what is implemented today. Until v0.1.0 ships, every object below
> exists only as an honest placeholder raising `NotImplementedError`.

## Usage

```python
from flowspec import Compiler

compiler = Compiler(tools="tools.yaml")

result = compiler.compile("workflow.yaml")

if result.success:
    print("Compilation successful")
    print(result.ir)
else:
    for diagnostic in result.diagnostics:
        print(diagnostic.message)
```

## Core objects

| Object | Role |
| ------ | ---- |
| `Compiler` | Facade: load registries, parse, compile, export |
| `CompilerConfig` | Strict typing, cycle detection, permissions, IR options |
| `Workflow` | Parsed workflow representation |
| `ToolDefinition` | A tool's declared contract |
| `ToolRegistry` | The set of known tools |
| `Type` | FlowSpec type values |
| `TypeChecker` | Compatibility checking |
| `WorkflowGraph` | Dependency graph with adjacency and reverse adjacency |
| `Diagnostic` | Structured error information |
| `CompilationResult` | Success with IR, or failure with diagnostics |
| `IntermediateRepresentation` | Versioned, deterministic compiled output |

## Compiler methods

```python
compiler.parse()      # Parse a workflow
compiler.analyze()    # Run analysis passes
compiler.compile()   # Full pipeline
compiler.explain()    # Dependency and parameter origins
compiler.export_ir()  # Emit the IR
```

## Exit codes (CLI)

| Code | Meaning |
| ---- | ------- |
| 0 | Compilation successful |
| 1 | Compilation errors |
| 2 | Syntax or configuration error |
| 3 | Integration error |
| 4 | Internal compiler error |
| 5 | Invalid CLI usage |

## Stability

The public API is versioned. Breaking changes only happen in major
releases; the workflow schema and IR carry explicit `version` fields and
are never silently broken.
