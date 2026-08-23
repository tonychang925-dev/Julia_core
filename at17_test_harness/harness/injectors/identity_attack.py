"""Identity authority attack injection.

AT17-R1-001: Registry Identity Creation.

Attack intent:

    Package Version → Identity Creation
    (Artifact → Identity Source)

The injector routes `create_identity` through the boundary guard. It never
touches the underlying component state directly; it only presents the
unauthorized operation request to the guard.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AttackRequest:
    """A single unauthorized operation attempt."""

    operation: str
    component: str
    params: dict


@dataclass
class AttackResult:
    attack_id: str
    request: AttackRequest
    response: object


class IdentityAttackInjector:
    """Injects identity-authority escalation attempts."""

    def __init__(self, guard) -> None:
        self._guard = guard

    def launch(self, attack_id: str, operation: str, **params) -> AttackResult:
        """Present an unauthorized operation to the guard and capture the verdict."""
        request = AttackRequest(
            operation=operation,
            component=self._guard.component,
            params=params,
        )
        response = self._guard.check_request(request.operation, **request.params)
        return AttackResult(
            attack_id=attack_id,
            request=request,
            response=response,
        )
