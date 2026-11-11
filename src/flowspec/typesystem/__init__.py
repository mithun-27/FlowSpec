"""FlowSpec's own type system.

Built independently from Pydantic and JSON Schema: those validate external
structures, while this package owns semantic type checking. Checking is
deterministic; an LLM never participates.

Status: implemented for the v0.1.0 compiler foundation; see
``docs/PROGRESS.md``.
"""
