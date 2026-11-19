"""FlowSpec's own type system.

Built independently from Pydantic and JSON Schema: those validate external
structures, while this package owns semantic type checking. Checking is
deterministic; an LLM never participates.

Every type is represented by a ``Type`` instance, and every compatibility
decision goes through the central ``TypeChecker``. Passes must not add
ad-hoc comparisons — one rule engine keeps diagnostics consistent across
inference, checking, and unification.

Status: implemented for the v0.1.0 compiler foundation; see
``docs/PROGRESS.md``.
"""
