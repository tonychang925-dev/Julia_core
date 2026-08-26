"""Permission Policy — Capability-level access control.

Controls WHAT Julia is ALLOWED to do, not HOW to do it.

C-08 canonical authorization now returns AuthorizationDecision. Existing callers
may still use ``allowed, reason = policy.check(scope)`` through an explicit
compatibility projection; the tuple is not the canonical authorization contract.
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator


class AuthorizationStatus(str, Enum):
    """C-08 authorization decision space."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    REQUIRE_ELEVATION = "REQUIRE_ELEVATION"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """First-class C-08 authorization decision.

    ``decision`` is the canonical authority. The iterator exists only so legacy
    code can continue doing ``allowed, reason = policy.check(scope)`` during the
    staged migration.
    """

    decision: str | AuthorizationStatus
    scope: str
    reason: str = ""
    policy_ref: str = "default"
    requested_at: str = field(default_factory=lambda: _iso_timestamp())
    provenance: dict = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.decision == AuthorizationStatus.ALLOW or self.decision == AuthorizationStatus.ALLOW.value

    def __iter__(self) -> Iterator[bool | str]:
        """Legacy compatibility: ``allowed, reason = decision``."""
        yield self.allowed
        yield self.reason


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """One permission rule for a capability scope."""
    scope: str                     # "market.observe", "system.read", "trade.execute"
    allow: bool
    reason: str = ""               # Why allowed/denied

    def to_decision(self, *, policy_ref: str = "default") -> AuthorizationDecision:
        return AuthorizationDecision(
            decision=AuthorizationStatus.ALLOW if self.allow else AuthorizationStatus.DENY,
            scope=self.scope,
            reason=self.reason,
            policy_ref=policy_ref,
            provenance={"source": "PermissionRule", "compat_allow_bool": self.allow},
        )


@dataclass
class PermissionPolicy:
    """Controls what capabilities Julia can invoke.

    Current defaults remain M0-compatible. The canonical API is
    AuthorizationDecision; tuple-unpack is transitional compatibility only.
    """

    rules: dict[str, PermissionRule] = field(default_factory=dict)
    policy_ref: str = "default"

    @classmethod
    def with_defaults(cls) -> "PermissionPolicy":
        """Create policy with M0 default rules."""
        return cls(rules={
            "system.read":     PermissionRule("system.read", allow=True,
                               reason="System information is read-only"),
            "market.observe":  PermissionRule("market.observe", allow=True,
                               reason="Read-only market observation"),
            "market.trade.execute": PermissionRule("market.trade.execute", allow=False,
                               reason="Julia never trades — core safety boundary"),
            "file.read":       PermissionRule("file.read", allow=True,
                               reason="Read within allowed paths"),
            "file.write":      PermissionRule("file.write", allow=True,
                               reason="Write with path permission check"),
            "file.delete":     PermissionRule("file.delete", allow=False,
                               reason="Requires user confirmation"),
            "memory.delete":   PermissionRule("memory.delete", allow=False,
                               reason="Requires Tony explicit action"),
        })

    def check(self, scope: str) -> AuthorizationDecision:
        """Return a first-class AuthorizationDecision.

        Unknown scopes default to DENY. Legacy callers may still unpack the
        returned decision as ``allowed, reason``.
        """
        if scope in self.rules:
            return self.rules[scope].to_decision(policy_ref=self.policy_ref)
        return AuthorizationDecision(
            decision=AuthorizationStatus.DENY,
            scope=scope,
            reason=f"unknown scope '{scope}' — denied by default",
            policy_ref=self.policy_ref,
            provenance={"source": "PermissionPolicy", "rule": "default_deny"},
        )

    def add_rule(self, rule: PermissionRule):
        self.rules[rule.scope] = rule

    def remove_scope(self, scope: str):
        self.rules.pop(scope, None)


def _iso_timestamp() -> str:
    return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())


__all__ = [
    "AuthorizationDecision",
    "AuthorizationStatus",
    "PermissionPolicy",
    "PermissionRule",
]
