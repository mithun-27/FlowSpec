"""Execution planning and runtime (optional module).

Execution is separate from compilation and never implicitly triggered by
it. Submodules:

- ``planner`` — turn validated IR into a concrete execution plan.
- ``runtime`` — explicit runtime invocation of compiled workflows.
- ``adapters`` — dispatch to MCP / REST / Python tool backends.

Status: planned (post-v0.1.0); see ``docs/PROGRESS.md``.
"""
