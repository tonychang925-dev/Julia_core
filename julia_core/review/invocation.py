"""Manual / explicit external code review invocation path.

Invocation is OPERATOR-TRIGGERED ONLY. There is zero automatic cognitive
routing here: nothing scans user text, nothing selects this capability on
behalf of cognition. Callers explicitly build a ReviewBundle and submit it.

The CapabilityRequest projected here carries ONLY semantic review data. It must
never carry browser session authority (tab_id, DOM selector, conversation URL,
extension nonce, browser command). Browser binding belongs to the provider /
transport layer.
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass
from typing import Any

from julia_core.capability.manager import CapabilityExecution, CapabilityManager
from julia_core.capability.models import CapabilityRequest
from julia_core.review.contracts import ReviewBundle, ReviewErrorCode
from julia_core.review.digest import compute_bundle_digest

EXTERNAL_REVIEW_CAPABILITY = "engineering.code_review"
EXTERNAL_REVIEW_SCOPE = "engineering.review.external"

# Fields a Core-side request MUST NOT carry: browser/transport authority.
_FORBIDDEN_AUTHORITY_KEYS = {
    "tab_id",
    "tab_ref",
    "dom_selector",
    "conversation_url",
    "chatgpt_url",
    "extension_nonce",
    "browser_command",
    "browser_session_id",
    "browser_session_ref",
}


class BrowserAuthorityInRequestError(ValueError):
    """Raised when review request arguments attempt to carry browser authority."""


def build_review_request(
    bundle: ReviewBundle,
    *,
    correlation_id: str = "",
    idempotency_key: str = "",
    turn_id: str = "",
    generation_id: str = "",
    requested_at: str | None = None,
) -> CapabilityRequest:
    """Project a ReviewBundle into a canonical CapabilityRequest.

    Only semantic review data crosses the boundary. Browser/session authority
    fields are rejected before projection (fail closed).
    """
    errors = bundle.validate()
    if errors:
        raise ValueError(f"{ReviewErrorCode.BUNDLE_SCHEMA_INVALID.value}: {'; '.join(errors)}")

    arguments: dict[str, Any] = {
        "review_id": bundle.review_id,
        "task_id": bundle.task_id,
        "candidate_id": bundle.candidate_id,
        "candidate_sha": bundle.candidate_sha,
        "repository": bundle.repository,
        "branch": bundle.branch,
        "review_mode": bundle.review_mode,
        "objective": bundle.objective,
        "acceptance_criteria": list(bundle.acceptance_criteria),
        "changed_files": list(bundle.changed_files),
        "diff_summary": bundle.diff_summary,
        "diff_blocks": [dict(b) for b in bundle.diff_blocks],
        "tests": list(bundle.tests),
        "known_risks": list(bundle.known_risks),
        "architecture_constraints": list(bundle.architecture_constraints),
        "questions": list(bundle.questions),
        "evidence_refs": list(bundle.evidence_refs),
        "limits": dict(bundle.limits),
        "identity_projection": dict(bundle.identity_projection),
        "bundle_digest": compute_bundle_digest(bundle),
    }

    forbidden = sorted(_find_forbidden_authority_keys(arguments))
    if forbidden:
        raise BrowserAuthorityInRequestError(
            f"browser authority fields are not allowed in Core review request: {forbidden}"
        )

    request = CapabilityRequest(
        capability_id=EXTERNAL_REVIEW_CAPABILITY,
        arguments=arguments,
        requested_scope=EXTERNAL_REVIEW_SCOPE,
        idempotency_key=idempotency_key or f"review:{bundle.review_id}",
        turn_id=turn_id,
        generation_id=generation_id,
        correlation_id=correlation_id,
        requested_at=requested_at,
        provenance={
            "invocation": "manual",
            "review_semantic": True,
            "browser_authority": "NONE",
            "source": "julia_core.review.invocation",
        },
    )
    return request


def _find_forbidden_authority_keys(value: Any) -> set[str]:
    """Recursively find browser/session authority keys anywhere in the payload.

    Browser authority must never cross the Core semantic boundary, including
    nested structures (diff_blocks, notes, limits). Fail closed on any hit.
    """
    found: set[str] = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                if str(key) in _FORBIDDEN_AUTHORITY_KEYS:
                    found.add(str(key))
                stack.append(child)
        elif isinstance(current, (list, tuple, set)):
            stack.extend(current)
    return found


@dataclass(frozen=True, slots=True)
class ReviewInvocationResult:
    """Typed result of one manual external review submission.

    Carries the exact CapabilityExecution from the Manager plus the semantic
    correlation digest for audit. Never flattens to a legacy string.
    """

    execution: CapabilityExecution
    bundle_digest: str

    @property
    def tool_result(self):
        return self.execution.tool_result

    @property
    def outcome_status(self) -> str:
        result = self.execution.tool_result
        if result is None:
            return "denied"
        return result.status.value if hasattr(result.status, "value") else str(result.status)

    @property
    def side_effect_state(self) -> str:
        result = self.execution.tool_result
        if result is None:
            return "none"
        return result.side_effect_state.value if hasattr(result.side_effect_state, "value") else str(result.side_effect_state)


async def submit_review(
    manager: CapabilityManager,
    bundle: ReviewBundle,
    *,
    correlation_id: str = "",
    turn_id: str = "",
    generation_id: str = "",
) -> ReviewInvocationResult:
    """Execute one review through the canonical CapabilityManager (typed path).

    Explicit manual invocation. The Manager enforces provider resolution,
    health, single execution, and typed outcome truth. Returns the immutable
    CapabilityExecution — no legacy string transport, no fallback.
    """
    request = build_review_request(
        bundle,
        correlation_id=correlation_id,
        turn_id=turn_id,
        generation_id=generation_id,
    )
    execution = await manager.execute_typed(request)
    return ReviewInvocationResult(execution=execution, bundle_digest=compute_bundle_digest(bundle))


__all__ = [
    "BrowserAuthorityInRequestError",
    "EXTERNAL_REVIEW_CAPABILITY",
    "EXTERNAL_REVIEW_SCOPE",
    "ReviewInvocationResult",
    "build_review_request",
    "submit_review",
]
