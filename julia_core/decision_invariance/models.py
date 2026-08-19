"""DIA-8 R1 — Core Decision Invariance Contract.

Deterministically evaluates structured decision semantics against a DIA-7
ContinuityState. This module does not parse natural language, score style,
create continuity truth, mutate DIA-7 schemas, or invent priority relations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Protocol, runtime_checkable

from julia_core.continuity_projection import ContinuityState

CANONICAL_VERSION = "dia8-decision-invariance-v1"
SITUATION_DOMAIN_SEPARATOR = "julia_core.decision_invariance.situation.v1"
CANDIDATE_DOMAIN_SEPARATOR = "julia_core.decision_invariance.candidate.v1"
POLICY_DOMAIN_SEPARATOR = "julia_core.decision_invariance.policy.v1"
RESULT_DOMAIN_SEPARATOR = "julia_core.decision_invariance.result.v1"
EVIDENCE_BINDING_DOMAIN_SEPARATOR = "julia_core.decision_invariance.evidence_binding.v1"
EVALUATION_ALGORITHM_REVISION = "dia8-r1-deterministic-evaluation-v2"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _require_sha256_hex(name: str, value: object) -> None:
    _require_non_empty_str(name, value)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a 64-character lowercase SHA-256 hex digest")


def _frame(value: str) -> bytes:
    _require_non_empty_str("canonical field", value)
    encoded = value.encode("utf-8")
    return str(len(encoded)).encode("ascii") + b":" + encoded + b"\n"


def _field(name: str, value: str) -> bytes:
    return _frame(name) + _frame(value)


def _digest_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


class DecisionConsistencyStatus(Enum):
    CONSISTENT = "consistent"
    DRIFT = "drift"
    UNDERDETERMINED = "underdetermined"


@dataclass(frozen=True)
class DecisionEvidenceBinding:
    claim_id: str
    lineage_digest: str
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("DecisionEvidenceBinding.claim_id", self.claim_id)
        _require_sha256_hex("DecisionEvidenceBinding.lineage_digest", self.lineage_digest)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("DecisionEvidenceBinding.schema_version is frozen")

    def canonical_bytes(self) -> bytes:
        return (
            _field("evidence_binding.domain", EVIDENCE_BINDING_DOMAIN_SEPARATOR)
            + _field("evidence_binding.schema_version", self.schema_version)
            + _field("evidence_binding.claim_id", self.claim_id)
            + _field("evidence_binding.lineage_digest", self.lineage_digest)
        )


@dataclass(frozen=True)
class DecisionSituation:
    situation_id: str
    situation_kind: str
    required_claim_ids: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    required_priority_relation: str = "none"
    unresolved_claim_ids: tuple[str, ...] = ()
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("DecisionSituation.situation_id", self.situation_id)
        _require_non_empty_str("DecisionSituation.situation_kind", self.situation_kind)
        _require_tuple("DecisionSituation.required_claim_ids", self.required_claim_ids)
        _require_tuple("DecisionSituation.allowed_actions", self.allowed_actions)
        _require_tuple("DecisionSituation.forbidden_actions", self.forbidden_actions)
        _require_tuple("DecisionSituation.unresolved_claim_ids", self.unresolved_claim_ids)
        for name in ("required_claim_ids", "allowed_actions", "forbidden_actions", "unresolved_claim_ids"):
            values = getattr(self, name)
            if not all(type(item) is str and item.strip() for item in values):
                raise ValueError(f"DecisionSituation.{name} must contain non-empty str only")
            if len(set(values)) != len(values):
                raise ValueError(f"DecisionSituation.{name} must not contain duplicates")
            object.__setattr__(self, name, tuple(sorted(values)))
        _require_non_empty_str("DecisionSituation.required_priority_relation", self.required_priority_relation)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("DecisionSituation.schema_version is frozen")

    def canonical_bytes(self) -> bytes:
        out = (
            _field("situation.domain", SITUATION_DOMAIN_SEPARATOR)
            + _field("situation.schema_version", self.schema_version)
            + _field("situation.id", self.situation_id)
            + _field("situation.kind", self.situation_kind)
            + _field("situation.required_priority_relation", self.required_priority_relation)
            + _field("situation.required_claim_count", str(len(self.required_claim_ids)))
        )
        for claim_id in self.required_claim_ids:
            out += _field("situation.required_claim_id", claim_id)
        out += _field("situation.allowed_action_count", str(len(self.allowed_actions)))
        for action in self.allowed_actions:
            out += _field("situation.allowed_action", action)
        out += _field("situation.forbidden_action_count", str(len(self.forbidden_actions)))
        for action in self.forbidden_actions:
            out += _field("situation.forbidden_action", action)
        out += _field("situation.unresolved_claim_count", str(len(self.unresolved_claim_ids)))
        for claim_id in self.unresolved_claim_ids:
            out += _field("situation.unresolved_claim_id", claim_id)
        return out

    def situation_digest(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True)
class CandidateDecision:
    decision_id: str
    stance: str
    action: str
    accepted_claim_ids: tuple[str, ...]
    rejected_claim_ids: tuple[str, ...]
    priority_applied: str
    conflict_status: str
    evidence_bindings: tuple[DecisionEvidenceBinding, ...]
    surface_text: str = "surface-may-vary"
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        for name in ("decision_id", "stance", "action", "priority_applied", "conflict_status", "surface_text"):
            _require_non_empty_str(f"CandidateDecision.{name}", getattr(self, name))
        _require_tuple("CandidateDecision.accepted_claim_ids", self.accepted_claim_ids)
        _require_tuple("CandidateDecision.rejected_claim_ids", self.rejected_claim_ids)
        _require_tuple("CandidateDecision.evidence_bindings", self.evidence_bindings)
        for name in ("accepted_claim_ids", "rejected_claim_ids"):
            values = getattr(self, name)
            if not all(type(item) is str and item.strip() for item in values):
                raise ValueError(f"CandidateDecision.{name} must contain non-empty str only")
            if len(set(values)) != len(values):
                raise ValueError(f"CandidateDecision.{name} must not contain duplicates")
            object.__setattr__(self, name, tuple(sorted(values)))
        if set(self.accepted_claim_ids) & set(self.rejected_claim_ids):
            raise ValueError("CandidateDecision accepts and rejects same claim")
        if not all(type(item) is DecisionEvidenceBinding for item in self.evidence_bindings):
            raise ValueError("CandidateDecision.evidence_bindings must contain DecisionEvidenceBinding only")
        bindings = tuple(sorted(self.evidence_bindings, key=lambda item: (item.claim_id, item.lineage_digest)))
        if len(set((item.claim_id, item.lineage_digest) for item in bindings)) != len(bindings):
            raise ValueError("CandidateDecision.evidence_bindings must not contain duplicates")
        object.__setattr__(self, "evidence_bindings", bindings)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("CandidateDecision.schema_version is frozen")

    def semantic_canonical_bytes(self) -> bytes:
        out = (
            _field("candidate.domain", CANDIDATE_DOMAIN_SEPARATOR)
            + _field("candidate.schema_version", self.schema_version)
            + _field("candidate.id", self.decision_id)
            + _field("candidate.stance", self.stance)
            + _field("candidate.action", self.action)
            + _field("candidate.priority_applied", self.priority_applied)
            + _field("candidate.conflict_status", self.conflict_status)
            + _field("candidate.accepted_claim_count", str(len(self.accepted_claim_ids)))
        )
        for claim_id in self.accepted_claim_ids:
            out += _field("candidate.accepted_claim_id", claim_id)
        out += _field("candidate.rejected_claim_count", str(len(self.rejected_claim_ids)))
        for claim_id in self.rejected_claim_ids:
            out += _field("candidate.rejected_claim_id", claim_id)
        out += _field("candidate.evidence_binding_count", str(len(self.evidence_bindings)))
        for binding in self.evidence_bindings:
            out += _field("candidate.evidence_binding", binding.canonical_bytes().decode("utf-8"))
        return out

    def candidate_decision_digest(self) -> str:
        return _digest_hex(self.semantic_canonical_bytes())


@dataclass(frozen=True)
class DecisionInvariantPolicy:
    revision: str
    evaluation_algorithm_revision: str = EVALUATION_ALGORITHM_REVISION
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("DecisionInvariantPolicy.revision", self.revision)
        if self.evaluation_algorithm_revision != EVALUATION_ALGORITHM_REVISION:
            raise ValueError("DecisionInvariantPolicy.evaluation_algorithm_revision is not implemented")
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("DecisionInvariantPolicy.schema_version is frozen")

    def canonical_bytes(self) -> bytes:
        return (
            _field("policy.domain", POLICY_DOMAIN_SEPARATOR)
            + _field("policy.schema_version", self.schema_version)
            + _field("policy.revision", self.revision)
            + _field("policy.evaluation_algorithm_revision", self.evaluation_algorithm_revision)
        )

    def policy_fingerprint(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True, init=False)
class DecisionEvaluationResult:
    status: DecisionConsistencyStatus
    supporting_claim_ids: tuple[str, ...]
    violated_claim_ids: tuple[str, ...]
    unresolved_claim_ids: tuple[str, ...]
    applied_rules: tuple[str, ...]
    policy_fingerprint: str
    continuity_state_digest: str
    situation_digest: str
    candidate_decision_digest: str
    evaluation_digest: str
    schema_version: str

    def __init__(
        self,
        status: DecisionConsistencyStatus,
        supporting_claim_ids: tuple[str, ...],
        violated_claim_ids: tuple[str, ...],
        unresolved_claim_ids: tuple[str, ...],
        applied_rules: tuple[str, ...],
        policy: DecisionInvariantPolicy,
        state: ContinuityState,
        situation: DecisionSituation,
        candidate: CandidateDecision,
    ) -> None:
        if type(status) is not DecisionConsistencyStatus:
            raise ValueError("DecisionEvaluationResult.status must be DecisionConsistencyStatus")
        _validate_state_integrity(state)
        if type(policy) is not DecisionInvariantPolicy:
            raise ValueError("DecisionEvaluationResult.policy must be DecisionInvariantPolicy")
        if type(situation) is not DecisionSituation:
            raise ValueError("DecisionEvaluationResult.situation must be DecisionSituation")
        if type(candidate) is not CandidateDecision:
            raise ValueError("DecisionEvaluationResult.candidate must be CandidateDecision")
        for name, values in (("supporting_claim_ids", supporting_claim_ids), ("violated_claim_ids", violated_claim_ids), ("unresolved_claim_ids", unresolved_claim_ids), ("applied_rules", applied_rules)):
            _require_tuple(f"DecisionEvaluationResult.{name}", values)
            if not all(type(item) is str and item.strip() for item in values):
                raise ValueError(f"DecisionEvaluationResult.{name} must contain non-empty str only")
            object.__setattr__(self, name, tuple(sorted(values)))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "policy_fingerprint", policy.policy_fingerprint())
        object.__setattr__(self, "continuity_state_digest", state.continuity_state_digest)
        object.__setattr__(self, "situation_digest", situation.situation_digest())
        object.__setattr__(self, "candidate_decision_digest", candidate.candidate_decision_digest())
        object.__setattr__(self, "schema_version", CANONICAL_VERSION)
        object.__setattr__(self, "evaluation_digest", _digest_hex(self.canonical_bytes(include_digest=False)))

    def canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("result.domain", RESULT_DOMAIN_SEPARATOR)
            + _field("result.schema_version", self.schema_version)
            + _field("result.status", self.status.value)
            + _field("result.policy_fingerprint", self.policy_fingerprint)
            + _field("result.continuity_state_digest", self.continuity_state_digest)
            + _field("result.situation_digest", self.situation_digest)
            + _field("result.candidate_decision_digest", self.candidate_decision_digest)
            + _field("result.supporting_claim_count", str(len(self.supporting_claim_ids)))
        )
        for claim_id in self.supporting_claim_ids:
            out += _field("result.supporting_claim_id", claim_id)
        out += _field("result.violated_claim_count", str(len(self.violated_claim_ids)))
        for claim_id in self.violated_claim_ids:
            out += _field("result.violated_claim_id", claim_id)
        out += _field("result.unresolved_claim_count", str(len(self.unresolved_claim_ids)))
        for claim_id in self.unresolved_claim_ids:
            out += _field("result.unresolved_claim_id", claim_id)
        out += _field("result.applied_rule_count", str(len(self.applied_rules)))
        for rule in self.applied_rules:
            out += _field("result.applied_rule", rule)
        if include_digest:
            out += _field("result.digest", self.evaluation_digest)
        return out


class StrictDecisionInvariantEvaluator:
    def evaluate(
        self,
        state: ContinuityState,
        situation: DecisionSituation,
        candidate: CandidateDecision,
        policy: DecisionInvariantPolicy,
        *,
        expected_continuity_state_digest: str | None = None,
        expected_policy_fingerprint: str | None = None,
    ) -> DecisionEvaluationResult:
        _validate_state_integrity(state)
        if type(situation) is not DecisionSituation:
            raise ValueError("situation must be exact DecisionSituation")
        if type(candidate) is not CandidateDecision:
            raise ValueError("candidate must be exact CandidateDecision")
        if type(policy) is not DecisionInvariantPolicy:
            raise ValueError("policy must be exact DecisionInvariantPolicy")
        if expected_continuity_state_digest is not None and state.continuity_state_digest != expected_continuity_state_digest:
            raise ValueError("continuity state digest mismatch")
        if expected_policy_fingerprint is not None and policy.policy_fingerprint() != expected_policy_fingerprint:
            raise ValueError("decision invariant policy fingerprint mismatch")

        active_claims = {claim.claim_id: claim for claim in state.active_claims}
        unresolved_claims = {claim.claim_id: claim for claim in state.unresolved_conflicts}
        known_claim_ids = set(active_claims) | set(unresolved_claims)

        for claim_id in set(candidate.accepted_claim_ids) | set(candidate.rejected_claim_ids) | set(situation.required_claim_ids) | set(situation.unresolved_claim_ids):
            if claim_id not in known_claim_ids:
                raise ValueError("decision references foreign continuity claim")
        evidence_bound_claim_ids = {binding.claim_id for binding in candidate.evidence_bindings}
        unbound_accepted = set(candidate.accepted_claim_ids) - evidence_bound_claim_ids
        if unbound_accepted:
            raise ValueError("accepted continuity claims require evidence binding")
        for binding in candidate.evidence_bindings:
            claim = active_claims.get(binding.claim_id) or unresolved_claims.get(binding.claim_id)
            if claim is None:
                raise ValueError("decision evidence binding references foreign claim")
            if binding.lineage_digest not in {ref.lineage_digest for ref in claim.supporting_evidence_refs}:
                raise ValueError("decision evidence binding lineage mismatch")

        applied_rules: list[str] = []
        supporting = set(candidate.accepted_claim_ids)
        violated = set()
        unresolved = set()

        missing_required = set(situation.required_claim_ids) - supporting
        if missing_required:
            unresolved.update(missing_required)
            applied_rules.append("REQUIRED_CLAIM_NOT_BOUND")

        if candidate.action in situation.forbidden_actions:
            violated.update(situation.required_claim_ids or candidate.accepted_claim_ids)
            applied_rules.append("FORBIDDEN_ACTION")

        if situation.unresolved_claim_ids:
            unresolved.update(situation.unresolved_claim_ids)
            if candidate.conflict_status != "PRESERVE_UNRESOLVED":
                violated.update(situation.unresolved_claim_ids)
                applied_rules.append("UNRESOLVED_CONFLICT_COLLAPSED")
            else:
                applied_rules.append("UNRESOLVED_CONFLICT_PRESERVED")

        if situation.required_priority_relation == "none":
            if len(situation.allowed_actions) > 1 and not violated and not situation.unresolved_claim_ids:
                applied_rules.append("MISSING_PRIORITY_UNDERDETERMINED")
                return DecisionEvaluationResult(
                    DecisionConsistencyStatus.UNDERDETERMINED,
                    tuple(supporting),
                    (),
                    tuple(unresolved or situation.required_claim_ids),
                    tuple(applied_rules),
                    policy,
                    state,
                    situation,
                    candidate,
                )
        else:
            priority_authority_claim_ids = _priority_authority_claim_ids(
                active_claims,
                candidate.evidence_bindings,
                situation.required_priority_relation,
            )
            if not priority_authority_claim_ids:
                applied_rules.append("PRIORITY_AUTHORITY_UNDERDETERMINED")
                return DecisionEvaluationResult(
                    DecisionConsistencyStatus.UNDERDETERMINED,
                    tuple(supporting),
                    (),
                    tuple(unresolved or situation.required_claim_ids),
                    tuple(applied_rules),
                    policy,
                    state,
                    situation,
                    candidate,
                )
            supporting.update(priority_authority_claim_ids)
            if candidate.priority_applied != situation.required_priority_relation:
                violated.update(priority_authority_claim_ids or situation.required_claim_ids or candidate.accepted_claim_ids)
                applied_rules.append("PRIORITY_RELATION_VIOLATED")
            else:
                applied_rules.append("PRIORITY_AUTHORITY_BOUND")
                applied_rules.append("PRIORITY_RELATION_APPLIED")

        if violated:
            return DecisionEvaluationResult(
                DecisionConsistencyStatus.DRIFT,
                tuple(supporting),
                tuple(violated),
                tuple(unresolved),
                tuple(applied_rules),
                policy,
                state,
                situation,
                candidate,
            )
        if missing_required:
            return DecisionEvaluationResult(
                DecisionConsistencyStatus.UNDERDETERMINED,
                tuple(supporting),
                (),
                tuple(unresolved),
                tuple(applied_rules),
                policy,
                state,
                situation,
                candidate,
            )
        if candidate.action not in situation.allowed_actions:
            return DecisionEvaluationResult(
                DecisionConsistencyStatus.UNDERDETERMINED,
                tuple(supporting),
                (),
                tuple(unresolved),
                tuple(applied_rules + ["ACTION_NOT_CONSTRAINED_BY_SITUATION"]),
                policy,
                state,
                situation,
                candidate,
            )
        applied_rules.append("DECISION_WITHIN_CONTINUITY_BOUNDS")
        return DecisionEvaluationResult(
            DecisionConsistencyStatus.CONSISTENT,
            tuple(supporting),
            (),
            tuple(unresolved),
            tuple(applied_rules),
            policy,
            state,
            situation,
            candidate,
        )


@runtime_checkable
class DecisionInvariantEvaluator(Protocol):
    def evaluate(self, state: ContinuityState, situation: DecisionSituation, candidate: CandidateDecision, policy: DecisionInvariantPolicy) -> DecisionEvaluationResult:
        ...


def _priority_authority_claim_ids(active_claims: dict[str, object], evidence_bindings: tuple[DecisionEvidenceBinding, ...], required_priority_relation: str) -> set[str]:
    token = "priority=" + required_priority_relation.lower()
    bound_claim_ids = {binding.claim_id for binding in evidence_bindings}
    authorized: set[str] = set()
    for claim_id in bound_claim_ids:
        claim = active_claims.get(claim_id)
        if claim is not None and getattr(claim, "claim_payload", "") == token:
            authorized.add(claim_id)
    return authorized


def _validate_state_integrity(state: ContinuityState) -> None:
    if type(state) is not ContinuityState:
        raise ValueError("expected exact ContinuityState")
    if _digest_hex(state.semantic_canonical_bytes(include_digest=False)) != state.continuity_state_digest:
        raise ValueError("continuity state digest mismatch")
