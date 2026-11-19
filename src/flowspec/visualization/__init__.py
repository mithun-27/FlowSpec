"""Workflow visualization and export.

Submodules:

- ``graph_renderer`` — render dependency graphs (Graphviz-backed).
  Planned for v0.4.0; not implemented yet.
- ``exporters`` — export compiled IR and compilation results as
  deterministic JSON. Implemented for the v0.1.0 compiler foundation.

Deterministic JSON means sorted keys, no timestamps, and values derived
only from the compilation input — the same workflow always produces
byte-for-byte identical output, which makes exports diff-friendly.

See ``docs/PROGRESS.md``.
"""
