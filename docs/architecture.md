# Architecture

> **Design document — implementation pending.** This document describes
> the planned architecture of FlowSpec v0.1.0 and later. See
> [PROGRESS.md](PROGRESS.md) for what is implemented today.

## Core philosophy

Treat AI agent workflows as **programs**, not arbitrary sequences of tool
calls. The compiler must validate the program before the execution engine
is allowed to run it.

FlowSpec validates **static** properties: declared contracts, types,
references, dependency structure. It does not guarantee runtime success —
an API being offline, invalid credentials, or a record not existing are
runtime concerns. Compilation is also never authorization.

## Products

FlowSpec is four connected products:

| Product | Role |
| ------- | ---- |
| **FlowSpec Core** | The compiler library: parsing, AST, type system, symbol resolution, semantic analysis, dependency analysis, IR generation |
| **FlowSpec CLI** | Typer/Rich developer interface over Core |
| **FlowSpec Integrations** | MCP, OpenAPI, and Python tool imports; agent framework adapters |
| **FlowSpec Playground** | Optional browser interface — must reuse Core, never re-implement it |

## Compilation pipeline

```text
          USER / AI AGENT
                 |
                 v
        WORKFLOW DEFINITION (YAML / JSON)
                 |
                 v
          SOURCE PARSER (P0–P2)
                 |
                 v
       NAME RESOLUTION / SEMANTIC ANALYSIS (P3–P4)
                 |
                 v
       TYPE INFERENCE / TYPE CHECKING (P5–P6)
                 |
                 v
       DEPENDENCY ANALYSIS / GRAPH ANALYSIS (P7–P8)
                 |
                 v
       DATAFLOW / CONSTRAINT / EFFECT ANALYSIS (P9–P11)
                 |
                 v
          COMPILER RESULT
                 |
          +------+------+
          |             |
          v             v
        VALID         INVALID
          |             |
          v             v
       IR OUTPUT     DIAGNOSTICS
          |
          v
    EXECUTION PLANNER (separate, optional)
          |
          v
    EXECUTION ADAPTERS (MCP / REST / Python)
```

Details of each pass are in [compiler_pipeline.md](compiler_pipeline.md).

## Package layout

The source follows a `src/` layout; every major component has its own
package:

```text
src/flowspec/
├── parser/        # YAML/JSON loading, validation, AST building
├── ast/           # Format-independent AST nodes and visitors
├── typesystem/    # Types, parsing, symbols, inference, unification, checking
├── registry/      # Tool registry and schema loading/normalization
├── semantic/      # Name resolution, semantic analysis
├── graph/         # Dependency graph, cycles, topological sort, scheduling
├── analysis/      # Static analyzers, constraints, effects, permissions
├── compiler/      # Pipeline orchestration, IR, results
├── diagnostics/   # Diagnostic model, error codes, formatting
├── integrations/  # MCP, OpenAPI, Python tools, LangGraph, LangChain
├── execution/     # Execution planning, runtime, adapters (optional)
└── visualization/ # Graph rendering, exporters
```

## Architectural invariants

1. **Compilation never executes tools.** Only explicit runtime invocation
   may execute tools.
2. **The core compiler never depends on Rich.** Terminal formatting lives
   in the CLI layer.
3. **Type checking is central and deterministic.** Compatibility rules live
   in one engine; no LLM participates in compiler decisions.
4. **Every pass is an independent, testable module** — no monolithic
   compiler file.
5. **Invalid workflows never produce executable IR.**
6. **Framework-specific logic stays out of the core** — integrations
   convert to FlowSpec's canonical AST/IR.
7. **Workflow files and external schemas are untrusted input** — safe
   parsing, size and depth limits, no arbitrary object construction.
8. **Deterministic output.** Identical inputs and configuration produce
   equivalent diagnostics and IR.
