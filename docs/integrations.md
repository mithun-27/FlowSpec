# Integrations

> **Design document — implementation pending (v0.3.0+).** This document
> describes the planned external integrations of FlowSpec. None of them
> exist yet. See [PROGRESS.md](PROGRESS.md) for what is implemented today.

## Model Context Protocol (MCP) — v0.3.0

```text
MCP Server → MCP Client → Tool Discovery → Schema Retrieval
          → Schema Normalization → FlowSpec Tool Registry
```

- Uses the official MCP Python SDK across supported transports.
- JSON Schema is normalized into FlowSpec types; unsupported constructs are
  **reported**, never silently ignored.
- Missing output contracts are marked unknown and require explicit
  annotation or a permissive mode.
- Tools are never executed during discovery; secrets never appear in
  diagnostics; credentials are never persisted in project files.

## OpenAPI 3.x — v0.3.0

Operations become FlowSpec tool definitions, including path/query
parameters, headers, request bodies, response schemas, enumerations,
resolvable references, and authentication metadata. API execution stays
separate from schema import.

## Python tools — v0.3.0

```python
from flowspec import tool

@tool
def get_customer(email: str) -> Customer:
    ...
```

Explicit registration is also available for functions without sufficient
annotations. Registered functions are never executed during compilation.

## Agent frameworks — v0.5.0

LangGraph and LangChain adapters convert framework-specific workflow
definitions into FlowSpec's canonical AST or IR. Framework-specific logic
never enters the core type system. Priority order: generic MCP → OpenAPI
→ Python tools → LangGraph → LangChain → community demand.
