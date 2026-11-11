# Changelog

All notable changes to FlowSpec are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- The v0.1.0 compiler foundation, fully implemented and tested:
  - Source loading with size and depth limits; safe YAML/JSON parsing;
    structural validation; and immutable, source-located AST construction.
  - Name resolution (order-independent, forward references allowed),
    semantic analysis, and tool registry loading from YAML/JSON schemas.
  - Type system: primitive, nominal, generic, and union types with a
    type expression parser, inference, deterministic unification, and
    compatibility checking (strict and permissive modes).
  - Dependency graph construction, cycle detection (E301), Kahn's
    topological sorting, and parallel execution stage scheduling.
  - Deterministic constraint analysis (P10) with seven rule kinds.
  - Versioned (`1.0`), deterministic intermediate representation with
    `to_dict`/`to_json` exports; compilation never executes tools.
  - CLI: `flowspec version`, `init`, `inspect`, `parse`, `compile`,
    `explain`, and `export`, with stable exit codes (0/1/2/4/5),
    `--tools`, `--verbose`, `--format text|json`, and `--emit-ir`;
    project configuration via a sibling `flowspec.yaml`.
  - Public Python API (`Compiler`, `CompilerConfig`,
    `CompilationPipeline`, `CompilationResult`,
    `IntermediateRepresentation`, `WorkflowNode`, `ToolDefinition`,
    `ToolRegistry`, `Type`, `TypeChecker`, `WorkflowGraph`,
    `Diagnostic`).
  - Structured diagnostics (E001–E601) with locations, expected/received
    values, and suggestions; deterministic JSON exporters.
- Test suite: 281 unit tests, 40 CLI integration tests, and Hypothesis
  property tests (generated valid workflows compile with order, staging,
  and determinism guarantees; random DAGs sort and stage correctly).
- Project scaffolding: `src/` package layout, packaging via Hatchling, and Ruff,
  pytest, mypy, and coverage configuration.
- Honest placeholder skeleton for every module not yet implemented. Each
  module documents its responsibility and raises `NotImplementedError` instead of
  simulating behavior — see `docs/PROGRESS.md` for the implementation roadmap.
- `flowspec` commands not implemented yet (`test`, `graph`,
  `validate-mcp`, `validate-openapi`) report that honestly and exit with
  code 4.
- Design documentation for the compiler pipeline, type system, workflow
  language, diagnostics, integrations, and public API, plus the implementation
  checklist (`docs/PROGRESS.md`).
- Example project `examples/invoice_processing` with valid and deliberately
  invalid workflow definitions taken from the specification; both compile
  (or fail, with six documented diagnostics) for real.
- CI workflow running Ruff and pytest on Linux and Windows for Python
  3.11–3.13, and a tag-triggered build workflow that produces distributions.
- Community files: Apache-2.0 `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`,
  issue templates, and a pull request template.
