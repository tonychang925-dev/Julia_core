"""GovernanceAuthorityMock — simulated governance environment (AT-17 Design §3).

The mock does NOT create Julia identity. It only exposes the authority
dependency interfaces a legitimate component may call. Its presence lets a
scenario distinguish "component obeyed governance" from "component attempted
to bypass governance".
"""

from __future__ import annotations


class GovernanceAuthorityMock:
    """Interface-only governance surface. Never an identity source."""

    def __init__(self) -> None:
        self._validation_calls: list[dict] = []

    def validate_artifact(self, package_id: str, version: str, ref: str) -> bool:
        """Interface: artifact validation dependency. Records, does not decide identity."""
        self._validation_calls.append(
            {"op": "validate_artifact", "package": package_id, "version": version, "ref": ref}
        )
        return True

    def approve_formation(self, *args, **kwargs):
        """Interface: formation approval belongs to governance. Not callable by registry."""
        raise RuntimeError("approve_formation is governance-only; component must not call it")

    def approve_evolution(self, *args, **kwargs):
        """Interface: evolution approval belongs to governance. Not callable by registry."""
        raise RuntimeError("approve_evolution is governance-only; component must not call it")

    def call_log(self) -> list[dict]:
        return list(self._validation_calls)
