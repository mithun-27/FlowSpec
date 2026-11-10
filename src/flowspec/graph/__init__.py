"""Dependency graph construction and analysis.

Submodules:

- ``graph`` — the ``WorkflowGraph`` data structure.
- ``dependency`` — dependency extraction and edge definitions.
- ``cycle_detection`` — circular dependency detection (E301).
- ``topological_sort`` — Kahn's algorithm execution ordering.
- ``reachability`` — reachability and dead-step analysis (E303).
- ``scheduler`` — parallel execution stage generation.

Status: planned for v0.1.0; see ``docs/PROGRESS.md``.
"""
