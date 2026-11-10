# FlowSpec Documentation

**FlowSpec is an open-source type system, static analysis engine, and
compiler for AI agent tool workflows.**

> Your agent plans it. FlowSpec proves it.

## Current status

**FlowSpec is in its scaffolding stage.** The repository currently
contains the complete project structure, packaging and CI configuration,
design documentation, and an honest placeholder skeleton for every
planned module. **The compiler itself is not implemented yet.**

- What actually works today: package installation, `flowspec version`,
  and the test/lint toolchain.
- What does not: every compiler feature — parsing, type checking,
  dependency analysis, diagnostics, and IR generation.
- See [PROGRESS.md](PROGRESS.md) for the live implementation checklist.

## Documentation map

| Document | Contents |
| -------- | -------- |
| [PROGRESS.md](PROGRESS.md) | Implementation checklist — what is real vs. planned |
| [getting_started.md](getting_started.md) | Installation and (future) first workflow |
| [architecture.md](architecture.md) | Product and system architecture |
| [compiler_pipeline.md](compiler_pipeline.md) | The P0–P12 compilation passes |
| [workflow_language.md](workflow_language.md) | YAML/JSON workflow and tool schemas |
| [type_system.md](type_system.md) | Types, nominal typing, compatibility rules |
| [error_codes.md](error_codes.md) | Diagnostic codes E001–E701 |
| [integrations.md](integrations.md) | MCP, OpenAPI, Python tools, agent frameworks |
| [api_reference.md](api_reference.md) | Planned public Python API |
| [contributing.md](contributing.md) | How to contribute |

All documents in this directory are **design documents** describing the
planned behavior of FlowSpec v0.1.0 and beyond. They are the contract the
implementation is being built against, not a description of shipped
features — each document states clearly what is implemented today.

## Example projects

See [`examples/invoice_processing`](../examples/invoice_processing/) in
the repository root for a complete sample project (valid and invalid
workflow definitions) that the compiler will validate once implemented.
