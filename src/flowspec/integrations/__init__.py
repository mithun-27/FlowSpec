"""External tool and framework integrations.

Adapters that connect FlowSpec with real external tools. Framework-specific
logic stays out of the core type system. Subpackages:

- ``mcp`` — MCP tool discovery and schema import (v0.3.0).
- ``openapi`` — OpenAPI 3.x specification import (v0.3.0).
- ``python`` — Python function tool registration (v0.3.0).
- ``langgraph`` — LangGraph workflow adapter (v0.5.0).
- ``langchain`` — LangChain workflow adapter (v0.5.0).

None of these integrations execute tools during discovery or compilation.

Status: planned; not implemented yet. See ``docs/PROGRESS.md``.
"""
