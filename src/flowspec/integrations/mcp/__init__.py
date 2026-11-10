"""Model Context Protocol (MCP) integration.

Planned pipeline: MCP server → client → tool discovery → schema retrieval
→ normalization → FlowSpec tool registry. Uses the official MCP Python
SDK. Output contracts that MCP servers do not provide are marked unknown
and require explicit annotation or a permissive mode.

Security invariants: tools are never executed during discovery, secrets are
never exposed in diagnostics, and credentials are never persisted in
project files.

Status: planned for v0.3.0; not implemented yet. See ``docs/PROGRESS.md``.
"""
