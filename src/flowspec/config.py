"""Compiler configuration for FlowSpec.

``CompilerConfig`` will carry the settings declared in a project's
``flowspec.yaml`` — strict typing, unknown-type policy, cycle detection,
permission validation, IR generation, and output paths — with validated
defaults and versioned schema handling.

Status: planned for v0.1.0. Not implemented yet; see ``docs/PROGRESS.md``.
"""

__all__ = ["CompilerConfig"]


class CompilerConfig:
    """Planned configuration object for the compiler pipeline.

    Raises ``NotImplementedError`` until the v0.1.0 compiler foundation is
    implemented.
    """

    def __init__(self) -> None:
        raise NotImplementedError(
            "CompilerConfig is planned for v0.1.0 and not implemented yet; see docs/PROGRESS.md"
        )
