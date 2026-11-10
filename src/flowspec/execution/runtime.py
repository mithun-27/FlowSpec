"""Workflow execution runtime.

Executes compiled workflows only through explicit runtime invocation —
never implicitly triggered by compilation. Runtime adapters independently
enforce credentials, access policies, and approvals; compilation is never
treated as authorization.

Status: planned; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["Runtime"]


class Runtime:
    """Placeholder for the workflow runtime. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("Runtime is planned; see docs/PROGRESS.md")
