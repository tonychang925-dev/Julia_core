"""M0.4 Permission Policy — Capability-level access control.

Controls WHAT Julia is ALLOWED to do, not HOW to do it.
Simple allow/deny rules for M0. Future: confirmation gates, rate limits, RBAC.

This is the enforcement layer for JULIA_CORE_PRINCIPLES.md P5:
Provider Output ≠ Identity Truth — nothing executes without permission.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """One permission rule for a capability scope."""
    scope: str                     # "market.observe", "system.read", "trade.execute"
    allow: bool
    reason: str = ""               # Why allowed/denied


@dataclass
class PermissionPolicy:
    """Controls what capabilities Julia can invoke.

    Simple key-based rules for M0. Designed for future extension:
      - require_confirmation: bool
      - rate_limit: "10/hour"
      - time_window: "09:00-15:00"
    """

    rules: dict[str, PermissionRule] = field(default_factory=dict)

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

    def check(self, scope: str) -> tuple[bool, str]:
        """Check if a permission scope is allowed.

        Returns (allowed, reason).
        Unknown scopes default to DENY.
        """
        if scope in self.rules:
            rule = self.rules[scope]
            return rule.allow, rule.reason
        # Unknown scope: deny by default (secure-by-default)
        return False, f"unknown scope '{scope}' — denied by default"

    def add_rule(self, rule: PermissionRule):
        self.rules[rule.scope] = rule

    def remove_scope(self, scope: str):
        self.rules.pop(scope, None)


__all__ = ["PermissionPolicy", "PermissionRule"]
