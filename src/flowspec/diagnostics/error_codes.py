"""The stable FlowSpec error code registry.

Codes are part of the public contract and must never be reused or
renamed. Registry (specification §13.1):

====== =============================================
Code   Meaning
====== =============================================
E001   Syntax error
E002   Invalid workflow structure
E101   Missing required dependency
E102   Unknown output reference
E103   Unresolved variable
E104   Invalid dependency
E201   Type mismatch
E202   Nominal type mismatch
E203   Type inference failure
E204   Nullable value violation
E205   Invalid generic type
E301   Circular dependency
E302   Invalid execution order
E303   Unreachable step
E304   Duplicate step ID
E401   Unknown tool
E402   Invalid tool argument
E403   Tool schema mismatch
E501   Missing permission
E502   Unsafe side-effect configuration
E601   Constraint violation
E701   IR generation failure
====== =============================================

Status: planned for v0.1.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["ErrorCodes"]


class ErrorCodes:
    """Placeholder for the error code registry. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError(
            "The error code registry is planned for v0.1.0; see docs/PROGRESS.md"
        )
