"""FlowSpec's own type system.

Built independently from Pydantic and JSON Schema: those validate external
structures, while this package owns semantic type checking. Submodules:

- ``types`` — primitive, nominal, generic, and structural type definitions.
- ``parser`` — parsing of type expressions (e.g. ``List[InvoiceID]``).
- ``symbols`` — symbol table for name resolution.
- ``inference`` — expression type inference.
- ``unification`` — deterministic type unification.
- ``type_checker`` — compatibility checking and assignment validation.

Status: planned for v0.1.0; see ``docs/PROGRESS.md``.
"""
