"""Opaque internal lifecycle capability (round-6 §A).

Underscore naming is NOT authority. A fake caller must not be able to mint
trusted invocation registration or retry-state sealing by calling internal
helpers with a genuine transaction + fabricated execution.

``ReviewLifecycleAuthority`` is an opaque single-use capability:

  - minted ONLY inside the controlled submit_review lifecycle;
  - bound to the exact transaction identity + exact execution fingerprint;
  - never returned in ReviewInvocationResult;
  - cannot be reconstructed from transaction IDs / strings / provenance
    (the token is a random secret held only in this module's registry);
  - single-use per gate (registration, outcome-seal).

Without a valid un-consumed authority, registration and sealing REJECT.
"""

from __future__ import annotations

import secrets
import threading
from typing import Any


class _LifecycleAuthority:
    __slots__ = ("_token",)

    def __init__(self, token: str):
        self._token = token

    @property
    def token(self) -> str:
        return self._token


_AUTHORITIES: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def mint_lifecycle_authority(*, transaction_id: str, execution_fingerprint: str) -> _LifecycleAuthority:
    """MINT ONLY inside the controlled submit_review lifecycle.

    Binds the opaque token to the exact transaction + execution fingerprint.
    """
    token = secrets.token_urlsafe(32)
    with _LOCK:
        _AUTHORITIES[token] = {
            "transaction_id": transaction_id,
            "execution_fingerprint": execution_fingerprint,
            "registration_used": False,
            "seal_used": False,
        }
    return _LifecycleAuthority(token)


def _authorize(
    authority: Any,
    *,
    gate: str,
    transaction_id: str,
    execution_fingerprint: str,
) -> bool:
    """Verify the authority matches the exact transaction+execution and consume
    the single-use gate. Returns False (never raises) on any mismatch."""
    if not isinstance(authority, _LifecycleAuthority):
        return False
    token = authority.token
    with _LOCK:
        entry = _AUTHORITIES.get(token)
        if entry is None:
            return False
        if entry["transaction_id"] != transaction_id:
            return False
        if entry["execution_fingerprint"] != execution_fingerprint:
            return False
        if entry[gate]:
            return False  # single-use gate already consumed
        entry[gate] = True
        return True


def authorize_registration(
    authority: Any,
    *,
    transaction_id: str,
    execution_fingerprint: str,
) -> bool:
    """Prove controlled lifecycle authority for invocation registration."""
    return _authorize(
        authority, gate="registration_used",
        transaction_id=transaction_id,
        execution_fingerprint=execution_fingerprint,
    )


def authorize_outcome_seal(
    authority: Any,
    *,
    transaction_id: str,
    execution_fingerprint: str,
) -> bool:
    """Prove controlled lifecycle authority for retry-state sealing."""
    return _authorize(
        authority, gate="seal_used",
        transaction_id=transaction_id,
        execution_fingerprint=execution_fingerprint,
    )


def _execution_fingerprint_of(execution: Any) -> str:
    """Canonical fingerprint of a CapabilityExecution's authority-bearing state.

    Bound inside mint_lifecycle_authority so a fabricated execution cannot
    satisfy the authority check.
    """
    import json as _json

    decision = execution.authorization_decision
    call = execution.capability_call
    tool = execution.tool_result

    def _plain(value):
        if isinstance(value, dict):
            return {k: _plain(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [_plain(v) for v in value]
        if hasattr(value, "value"):
            return value.value
        return value

    authority = {
        "authorization_decision": _plain({
            "decision": getattr(decision.decision, "value", decision.decision) if decision is not None else None,
            "scope": decision.scope if decision is not None else None,
        }),
        "capability_call": _plain({
            "capability_call_id": call.capability_call_id if call is not None else None,
            "capability_request_id": call.capability_request_id if call is not None else None,
            "status": getattr(call.status, "value", call.status) if call is not None else None,
            "provider": call.provider if call is not None else None,
            "correlation_id": call.correlation_id if call is not None else None,
        }),
        "tool_result": _plain({
            "capability_call_id": tool.capability_call_id if tool is not None else None,
            "status": getattr(tool.status, "value", tool.status) if tool is not None else None,
            "side_effect_state": getattr(tool.side_effect_state, "value", tool.side_effect_state) if tool is not None else None,
            "structured_output": tool.structured_output if tool is not None else None,
            "error": tool.error if tool is not None else None,
        }),
        "evidence": [
            _plain({
                "evidence_id": e.evidence_id,
                "source_ref": e.source_ref,
                "content_ref": e.content_ref,
                "provenance": e.provenance,
            })
            for e in execution.evidence
        ],
    }
    return _json.dumps(authority, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "_LifecycleAuthority",
    "authorize_outcome_seal",
    "authorize_registration",
    "mint_lifecycle_authority",
]
