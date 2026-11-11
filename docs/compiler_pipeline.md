# Compiler Pipeline

> **Implemented for the v0.1.0 compiler foundation** (P9 dataflow and
> P11 effect analysis are planned for v0.2.0). This document describes
> the compilation passes of FlowSpec. See [PROGRESS.md](PROGRESS.md)
> for the live status.

## Overview

Compilation runs twelve ordered passes (P0–P12). Each pass is an
independent, testable module. A failed **mandatory** pass prevents the
generation of executable IR; the compiler may still produce partial
diagnostics and a non-executable analysis report.

## Passes

| Pass | Name | Purpose |
| ---- | ---- | ------- |
| P0 | Source loading | Load YAML/JSON with size and depth limits |
| P1 | Syntax parsing | Parse workflow structure |
| P2 | AST construction | Build format-independent AST nodes |
| P3 | Name resolution | Resolve tools and references against the registry and symbol table |
| P4 | Semantic analysis | Validate declarations (unique IDs, supplied inputs, valid outputs) |
| P5 | Type inference | Infer expression types from declarations and contracts |
| P6 | Type checking | Validate assignments against the central compatibility rules |
| P7 | Dependency analysis | Extract dependency edges between steps |
| P8 | Graph analysis | Detect cycles and compute topological ordering |
| P9 | Dataflow analysis | Track value origins (v0.2.0) |
| P10 | Constraint analysis | Evaluate deterministic constraints |
| P11 | Effect analysis | Check side effects and permissions (v0.2.0) |
| P12 | IR generation | Emit the versioned intermediate representation |

## Ordering and independence

- Passes run in order; each receives the outputs of the previous passes.
- Declaration order in the source does **not** matter — forward references
  are permitted as long as the dependency graph remains valid.
- Diagnostics aggregate across passes before being reported; a pass that
  fails fast still contributes the diagnostics gathered so far.

## Result

| Outcome | Produced |
| ------- | -------- |
| Valid workflow | Versioned IR + dependency-aware execution plan (stages) |
| Invalid workflow | Structured diagnostics only; **no executable IR** |

## Static analyzers feeding the passes (v0.1.0 subset)

1. Missing input analyzer — every required tool input is supplied.
2. Reference analyzer — all references resolve to declared symbols.
3. Type analyzer — source types are compatible with destination types.
4. Dependency analyzer — required dependencies are available.
5. Cycle analyzer — no circular dependencies.
6. Output analyzer — workflow outputs reference valid expressions.
7. Optional value analyzer — nullable values never silently satisfy
   non-nullable parameters.

Later releases add reachability, effect, and permission analyzers. Each
analyzer returns structured diagnostics — never terminal output.
