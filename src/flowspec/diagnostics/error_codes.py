"""The stable FlowSpec error code registry.

Codes are part of the public contract and must never be reused or renamed.
Categories group the codes; every diagnostic produced anywhere in the
compiler carries one of these codes.

====== ============================================= ==========================
Code   Category                                      Meaning
====== ============================================= ==========================
E001   syntax                                        Syntax error
E002   structure                                     Invalid workflow structure
E101   dependency                                    Missing required dependency
E102   dependency                                    Unknown output reference
E103   dependency                                    Unresolved variable
E104   dependency                                    Invalid dependency
E201   type                                          Type mismatch
E202   type                                          Nominal type mismatch
E203   type                                          Type inference failure
E204   type                                          Nullable value violation
E205   type                                          Invalid generic type
E301   graph                                         Circular dependency
E302   graph                                         Invalid execution order
E303   graph                                         Unreachable step
E304   graph                                         Duplicate step ID
E401   tool                                          Unknown tool
E402   tool                                          Invalid tool argument
E403   tool                                          Tool schema mismatch
E501   security                                      Missing permission
E502   security                                      Unsafe side-effect configuration
E601   constraint                                    Constraint violation
E701   ir                                            IR generation failure
====== ============================================= ==========================

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from collections.abc import Mapping

__all__ = ["ErrorCodes"]

_REGISTRY: dict[str, tuple[str, str]] = {
    "E001": ("syntax", "Syntax error"),
    "E002": ("structure", "Invalid workflow structure"),
    "E101": ("dependency", "Missing required dependency"),
    "E102": ("dependency", "Unknown output reference"),
    "E103": ("dependency", "Unresolved variable"),
    "E104": ("dependency", "Invalid dependency"),
    "E201": ("type", "Type mismatch"),
    "E202": ("type", "Nominal type mismatch"),
    "E203": ("type", "Type inference failure"),
    "E204": ("type", "Nullable value violation"),
    "E205": ("type", "Invalid generic type"),
    "E301": ("graph", "Circular dependency"),
    "E302": ("graph", "Invalid execution order"),
    "E303": ("graph", "Unreachable step"),
    "E304": ("graph", "Duplicate step ID"),
    "E401": ("tool", "Unknown tool"),
    "E402": ("tool", "Invalid tool argument"),
    "E403": ("tool", "Tool schema mismatch"),
    "E501": ("security", "Missing permission"),
    "E502": ("security", "Unsafe side-effect configuration"),
    "E601": ("constraint", "Constraint violation"),
    "E701": ("ir", "IR generation failure"),
}


class ErrorCodes:
    """Stable error code constants and registry lookups."""

    # Syntax / structure
    SYNTAX = "E001"
    STRUCTURE = "E002"

    # Dependency
    MISSING_DEPENDENCY = "E101"
    UNKNOWN_OUTPUT_REFERENCE = "E102"
    UNRESOLVED_VARIABLE = "E103"
    INVALID_DEPENDENCY = "E104"

    # Type
    TYPE_MISMATCH = "E201"
    NOMINAL_TYPE_MISMATCH = "E202"
    TYPE_INFERENCE_FAILURE = "E203"
    NULLABLE_VIOLATION = "E204"
    INVALID_GENERIC_TYPE = "E205"

    # Graph
    CIRCULAR_DEPENDENCY = "E301"
    INVALID_EXECUTION_ORDER = "E302"
    UNREACHABLE_STEP = "E303"
    DUPLICATE_STEP_ID = "E304"

    # Tool
    UNKNOWN_TOOL = "E401"
    INVALID_TOOL_ARGUMENT = "E402"
    TOOL_SCHEMA_MISMATCH = "E403"

    # Security
    MISSING_PERMISSION = "E501"
    UNSAFE_EFFECT_CONFIGURATION = "E502"

    # Constraint / IR
    CONSTRAINT_VIOLATION = "E601"
    IR_GENERATION_FAILURE = "E701"

    @classmethod
    def all_codes(cls) -> tuple[str, ...]:
        """Every registered code, in sorted order."""
        return tuple(sorted(_REGISTRY))

    @classmethod
    def is_valid(cls, code: str) -> bool:
        """Report whether ``code`` exists in the registry."""
        return code in _REGISTRY

    @classmethod
    def category(cls, code: str) -> str:
        """The category of a registered code (unknown codes map to '')."""
        return _REGISTRY.get(code, ("", ""))[0]

    @classmethod
    def description(cls, code: str) -> str:
        """The human description of a registered code (unknown → '')."""
        return _REGISTRY.get(code, ("", ""))[1]

    @classmethod
    def registry(cls) -> Mapping[str, tuple[str, str]]:
        """The read-only code → (category, description) registry."""
        return _REGISTRY
