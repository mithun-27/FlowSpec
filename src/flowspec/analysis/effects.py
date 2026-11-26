"""Effect analysis.

Identifies declared ``read``, ``write``, ``external_write``,
``destructive``, ``financial``, ``network``, and ``unknown`` effects,
flags destructive tools and operations requiring confirmation, and
preserving effect information in the IR. Compilation is never treated as
authorization (E502).

Status: planned for v0.2.0; not implemented yet. See ``docs/PROGRESS.md``.

E502 is reserved for unsafe side-effect configuration. Today effect names
are validated as structure, but no effect policy is enforced.
"""

__all__ = ["EffectAnalyzer"]


class EffectAnalyzer:
    """Placeholder for the effect analyzer. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("EffectAnalyzer is planned for v0.2.0; see docs/PROGRESS.md")
