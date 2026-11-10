"""Permission analysis.

Checks whether the workflow's declared permissions satisfy tool
requirements (E501). Declared permissions are metadata, not proof of real
authorization — runtime adapters enforce credentials and access policies
independently.

Status: planned for v0.2.0; not implemented yet. See ``docs/PROGRESS.md``.
"""

__all__ = ["PermissionAnalyzer"]


class PermissionAnalyzer:
    """Placeholder for the permission analyzer. Not implemented yet."""

    def __init__(self) -> None:
        raise NotImplementedError("PermissionAnalyzer is planned for v0.2.0; see docs/PROGRESS.md")
