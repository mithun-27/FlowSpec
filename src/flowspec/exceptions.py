"""Structured exception hierarchy for FlowSpec.

All FlowSpec-specific exceptions derive from :class:`FlowSpecError` so that
callers can catch compiler failures without swallowing unrelated bugs.
Structured subcategories (parse, type, dependency, and integration errors)
will be introduced together with the compiler passes that raise them.

Status: only the base class exists. The hierarchy grows as compiler stages
are implemented; see ``docs/PROGRESS.md``.
"""

__all__ = ["FlowSpecError"]


class FlowSpecError(Exception):
    """Base class for all FlowSpec-specific errors."""
