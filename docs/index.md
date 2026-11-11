# FlowSpec Documentation

**FlowSpec is an open-source type system, static analysis engine, and
compiler for AI agent tool workflows.**

> Your agent plans it. FlowSpec proves it.

## Current status

**The v0.1.0 compiler foundation is implemented and green.** The full
pipeline — parsing, AST construction, name resolution, semantic
analysis, type inference and checking, dependency graphs, cycle
detection, topological scheduling, constraint analysis, and versioned
IR generation — works today, with a CLI (`flowspec init`, `inspect`,
`parse`, `compile`, `explain`, `export`) and a public Python API.

- What works today: the compiler core, the CLI, deterministic JSON IR
  export, and the test/lint toolchain.
- What does not yet: dataflow and effect analysis (v0.2.0), all
  integrations (v0.3.0+), graph rendering (v0.4.0), and the execution
  runtime.
- See [PROGRESS.md](PROGRESS.md) for the live implementation checklist.

## Documentation map

| Document | Contents |
| -------- | -------- |
| [PROGRESS.md](PROGRESS.md) | Implementation checklist — what is real vs. planned |
| [getting_started.md](getting_started.md) | Installation and compiling your first workflow |
| [architecture.md](architecture.md) | Product and system architecture |
| [compiler_pipeline.md](compiler_pipeline.md) | The P0–P12 compilation passes |
| [workflow_language.md](workflow_language.md) | YAML/JSON workflow and tool schemas |
| [type_system.md](type_system.md) | Types, nominal typing, compatibility rules |
| [error_codes.md](error_codes.md) | Diagnostic codes E001–E701 |
| [integrations.md](integrations.md) | MCP, OpenAPI, Python tools, agent frameworks |
| [api_reference.md](api_reference.md) | The public Python API |
| [contributing.md](contributing.md) | How to contribute |

The documents in this directory describe FlowSpec v0.1.0 and beyond.
The v0.1.0 compiler foundation described here is implemented; later
milestones remain design documents. Each document states clearly what
is implemented today.

## Example projects

See [`examples/invoice_processing`](../examples/invoice_processing/) in
the repository root for a complete sample project (valid and invalid
workflow definitions) that the compiler will validate once implemented.
