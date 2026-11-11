"""Type compatibility checking.

The **single central compatibility engine** for FlowSpec (specification
§6.5). Comparison logic lives here and nowhere else — no other compiler
module decides whether a source type satisfies a target type.

Rules (in evaluation order):

===== ========================= ==============================
Source Target                    Result
===== ========================= ==============================
T      T                         Valid (exact equality)
any    T / T any                 E203 in strict mode unless allowed
null   Optional[T]               Valid
null   T (non-optional)          E204
Opt[S] Opt[T]                    Valid iff S -> T
Opt[S] T                         E204 (nullability not proven)
S      Opt[T]                    Valid iff S -> T
int    float                      Valid with widening
float  int                        E201
prim   prim (different)           E201
Nom    Nom (different name)      E202
Nom    prim / prim Nom           E201
List   List                       parameter-wise
Dict   Dict                       parameter-wise
S      Union[...]                 Valid iff S matches a member
Union  T                          Valid iff every member -> T
Obj    Obj                        required properties present
===== ========================= ==============================

Status: implemented for the v0.1.0 compiler foundation.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowspec.config import CompilerConfig
from flowspec.diagnostics.error_codes import ErrorCodes
from flowspec.typesystem.types import (
    GenericType,
    NominalType,
    ObjectType,
    PrimitiveType,
    Type,
    is_any,
    is_null,
    is_optional,
    optional_of,
)

__all__ = ["CompatibilityResult", "TypeChecker"]


@dataclass(frozen=True)
class CompatibilityResult:
    """The outcome of one compatibility check."""

    compatible: bool
    code: str | None = None
    reason: str | None = None

    @property
    def failure_code(self) -> str:
        """The diagnostic code, or E201 when only a generic mismatch."""
        return self.code or ErrorCodes.TYPE_MISMATCH


class TypeChecker:
    """The central type compatibility engine."""

    def __init__(self, config: CompilerConfig | None = None) -> None:
        self.config = config or CompilerConfig()

    def check_assignment(self, source: Type, target: Type) -> CompatibilityResult:
        """Can a value of ``source`` be assigned where ``target`` is required?"""
        if source == target:
            return CompatibilityResult(True)

        if is_any(source) or is_any(target):
            if self.config.strict_types and not self.config.allow_unknown_types:
                return CompatibilityResult(
                    False,
                    ErrorCodes.TYPE_INFERENCE_FAILURE,
                    f"'any' is involved while strict typing is enabled "
                    f"({source.render()} -> {target.render()})",
                )
            return CompatibilityResult(True)

        if is_null(source):
            if is_optional(target):
                return CompatibilityResult(True)
            return CompatibilityResult(
                False,
                ErrorCodes.NULLABLE_VIOLATION,
                f"null cannot satisfy non-nullable {target.render()}",
            )

        if is_optional(source):
            if is_optional(target):
                return self.check_assignment(optional_of(source), optional_of(target))
            return CompatibilityResult(
                False,
                ErrorCodes.NULLABLE_VIOLATION,
                f"optional {source.render()} cannot satisfy non-nullable "
                f"{target.render()} without a null check",
            )
        if is_optional(target):
            return self.check_assignment(source, optional_of(target))

        if is_null(target):
            return CompatibilityResult(
                False, ErrorCodes.TYPE_MISMATCH, "only null can be assigned to null"
            )

        if isinstance(source, PrimitiveType) and isinstance(target, PrimitiveType):
            if source.name == "integer" and target.name == "float":
                return CompatibilityResult(True)
            return CompatibilityResult(
                False,
                ErrorCodes.TYPE_MISMATCH,
                f"{source.render()} is not compatible with {target.render()}",
            )

        if isinstance(source, NominalType) and isinstance(target, NominalType):
            return CompatibilityResult(
                False,
                ErrorCodes.NOMINAL_TYPE_MISMATCH,
                f"{source.render()} and {target.render()} are distinct nominal types",
            )

        if isinstance(source, NominalType) != isinstance(target, NominalType):
            return CompatibilityResult(
                False,
                ErrorCodes.TYPE_MISMATCH,
                f"{source.render()} is not compatible with {target.render()} "
                f"(nominal types never convert implicitly)",
            )

        if isinstance(source, GenericType) or isinstance(target, GenericType):
            return self._check_generic(source, target)

        if isinstance(source, ObjectType) and isinstance(target, ObjectType):
            return self._check_object(source, target)

        return CompatibilityResult(
            False,
            ErrorCodes.TYPE_MISMATCH,
            f"{source.render()} is not compatible with {target.render()}",
        )

    def _check_generic(self, source: Type, target: Type) -> CompatibilityResult:
        if isinstance(target, GenericType) and target.base == "Union":
            members = target.parameters
            if isinstance(source, GenericType) and source.base == "Union":
                for member in source.parameters:
                    if not any(
                        self.check_assignment(member, other).compatible for other in members
                    ):
                        return CompatibilityResult(
                            False,
                            ErrorCodes.TYPE_MISMATCH,
                            f"{member.render()} matches no member of {target.render()}",
                        )
                return CompatibilityResult(True)
            if any(self.check_assignment(source, other).compatible for other in members):
                return CompatibilityResult(True)
            return CompatibilityResult(
                False,
                ErrorCodes.TYPE_MISMATCH,
                f"{source.render()} matches no member of {target.render()}",
            )

        if isinstance(source, GenericType) and source.base == "Union":
            for member in source.parameters:
                result = self.check_assignment(member, target)
                if not result.compatible:
                    return result
            return CompatibilityResult(True)

        if not (isinstance(source, GenericType) and isinstance(target, GenericType)):
            return CompatibilityResult(
                False,
                ErrorCodes.TYPE_MISMATCH,
                f"{source.render()} is not compatible with {target.render()}",
            )

        if source.base != target.base:
            return CompatibilityResult(
                False,
                ErrorCodes.TYPE_MISMATCH,
                f"{source.render()} is not compatible with {target.render()}",
            )

        if len(source.parameters) != len(target.parameters):
            return CompatibilityResult(
                False,
                ErrorCodes.TYPE_MISMATCH,
                f"{source.render()} is not compatible with {target.render()} "
                f"(parameter counts differ)",
            )

        for source_parameter, target_parameter in zip(
            source.parameters, target.parameters, strict=True
        ):
            result = self.check_assignment(source_parameter, target_parameter)
            if not result.compatible:
                return result
        return CompatibilityResult(True)

    def _check_object(self, source: ObjectType, target: ObjectType) -> CompatibilityResult:
        for target_property in target.properties:
            source_property = source.property(target_property.name)
            if source_property is None:
                if target_property.required:
                    return CompatibilityResult(
                        False,
                        ErrorCodes.TYPE_MISMATCH,
                        f"missing required property {target_property.name!r} for {target.render()}",
                    )
                continue
            result = self.check_assignment(source_property.type, target_property.type)
            if not result.compatible:
                return result
        return CompatibilityResult(True)
