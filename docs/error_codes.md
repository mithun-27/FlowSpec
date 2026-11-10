# Error Codes

> **Design document — implementation pending.** This document describes
> the planned diagnostic codes of FlowSpec. See [PROGRESS.md](PROGRESS.md)
> for what is implemented today.

Diagnostic codes are part of FlowSpec's public contract: codes are stable,
never reused, and never renamed.

## Registry

| Code | Category | Meaning |
| ---- | -------- | ------- |
| E001 | Syntax | Syntax error |
| E002 | Structure | Invalid workflow structure |
| E101 | Dependency | Missing required dependency |
| E102 | Dependency | Unknown output reference |
| E103 | Dependency | Unresolved variable |
| E104 | Dependency | Invalid dependency |
| E201 | Type | Type mismatch |
| E202 | Type | Nominal type mismatch |
| E203 | Type | Type inference failure |
| E204 | Type | Nullable value violation |
| E205 | Type | Invalid generic type |
| E301 | Graph | Circular dependency |
| E302 | Graph | Invalid execution order |
| E303 | Graph | Unreachable step |
| E304 | Graph | Duplicate step ID |
| E401 | Tool | Unknown tool |
| E402 | Tool | Invalid tool argument |
| E403 | Tool | Tool schema mismatch |
| E501 | Security | Missing permission |
| E502 | Security | Unsafe side-effect configuration |
| E601 | Constraint | Constraint violation |
| E701 | IR | IR generation failure |

## Diagnostic shape

Every diagnostic carries:

- `code`, `severity` (error / warning / info / hint), `category`
- `message` and the workflow / step context
- `source_location` — file, line, and column where available
- `expected` and `received` values where relevant
- `suggestions` — deterministic correction candidates

Diagnostics are structured data, rendered by the CLI layer for humans
(Rich) and exportable as JSON for machines. The core compiler never
depends on terminal formatting libraries.
