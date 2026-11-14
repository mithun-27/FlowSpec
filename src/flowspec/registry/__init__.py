"""Tool registry and schema handling.

Submodules:

- ``tool_registry`` — the registry of known tools with their contracts.
- ``schema_loader`` — loading tool schemas from YAML/JSON files.
- ``schema_normalizer`` — normalizing external schemas (MCP, OpenAPI,
  Python annotations) into FlowSpec's internal type system.

Status: ``tool_registry`` and ``schema_loader`` are implemented for the
v0.1.0 compiler foundation; ``schema_normalizer`` is planned for
v0.3.0. See ``docs/PROGRESS.md``.
"""
