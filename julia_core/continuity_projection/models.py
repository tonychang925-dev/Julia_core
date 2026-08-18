"""DIA-7 R1 — Core Continuity Projection canonical contract.

Continuity projection is a deterministic materialized view over verified DIA-6
lineage artifacts. It is not new history, Memory, Diary, model prose,
persistence, or runtime state mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Protocol, runtime_checkable

from julia_core.context_evolution import ContextEvolutionKind, ContextLineageEdge

CANONICAL_VERSION = "dia7-continuity-projection-v1"
STATE_DOMAIN_SEPARATOR = "julia_core.continuity_projection.state.v1"
CLAIM_DOMAIN_SEPARATOR = "julia_core.continuity_projection.claim.v1"
EVIDENCE_DOMAIN_SEPARATOR = "julia_core.continuity_projection.evidence_ref.v1"
POLICY_DOMAIN_SEPARATOR = "julia_core.continuity_projection.policy.v1"
INPUT_DOMAIN_SEPARATOR = "julia_core.continuity_projection.input.v1"
PROJECTION_ALGORITHM_REVISION = "dia7-core-projection-v1"
STATE_DIGEST_ALGORITHM_REVISION = "dia7-state-digest-v1"
INPUT_CANONICALIZATION_REVISION = "dia7-input-canonicalization-v1"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _require_positive_int(name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive int")


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


class ContinuityClaimKind(Enum):
    IDENTITY_ANCHOR = "identity_anchor"
    STABLE_PREFERENCE = "stable_preference"
    RELATIONSHIP_STATE = "relationship_state"
    ACTIVE_COMMITMENT = "active_commitment"
    RESOLVED_BELIEF = "resolved_belief"
    UNRESOLVED_TENSION = "unresolved_tension"
    LONG_TERM_TRAIT = "long_term_trait"


class ContinuityConflictRule(Enum):
    APPEND = "append"
    SUPERSEDE = "supersede"
    CORRECT = "correct"
    DEPRECATE = "deprecate"
    UNRESOLVED = "unresolved"


class ContinuityClaimStatus(Enum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CORRECTED = "corrected"
    DEPRECATED = "deprecated"
    CONFLICTED = "conflicted"
    INSUFFICIENT_SUPPORT = "insufficient_support"


def _require_claim_kind(name: str, value: object) -> ContinuityClaimKind:
    if type(value) is ContinuityClaimKind:
        return value
    if type(value) is str:
        try:
            return ContinuityClaimKind(value)
        except ValueError as e:
            raise ValueError(f"{name} must be a frozen ContinuityClaimKind") from e
    raise ValueError(f"{name} must be ContinuityClaimKind")


def _require_conflict_rule(name: str, value: object) -> ContinuityConflictRule:
    if type(value) is ContinuityConflictRule:
        return value
    if type(value) is str:
        try:
            return ContinuityConflictRule(value)
        except ValueError as e:
            raise ValueError(f"{name} must be a frozen ContinuityConflictRule") from e
    raise ValueError(f"{name} must be ContinuityConflictRule")


def _require_claim_status(name: str, value: object) -> ContinuityClaimStatus:
    if type(value) is ContinuityClaimStatus:
        return value
    if type(value) is str:
        try:
            return ContinuityClaimStatus(value)
        except ValueError as e:
            raise ValueError(f"{name} must be a frozen ContinuityClaimStatus") from e
    raise ValueError(f"{name} must be ContinuityClaimStatus")


def _reject_duplicate_claim_ids(name: str, claims: tuple["ContinuityClaim", ...]) -> None:
    ids = [claim.claim_id for claim in claims]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{name} must not contain duplicate claim ids")


def _reject_duplicate_evidence_refs(name: str, refs: tuple["ContinuityEvidenceRef", ...]) -> None:
    keys = [ref.lineage_digest for ref in refs]
    if len(set(keys)) != len(keys):
        raise ValueError(f"{name} must not contain duplicate lineage evidence refs")


@dataclass(frozen=True, init=False)
class ContinuityEvidenceRef:
    lineage_digest: str
    parent_context_digest: str
    child_context_digest: str
    operation_id: str
    operation_kind: ContextEvolutionKind
    schema_version: str

    def __init__(self, edge: ContextLineageEdge) -> None:
        if type(edge) is not ContextLineageEdge:
            raise ValueError("ContinuityEvidenceRef requires exact DIA-6 ContextLineageEdge provenance")
        lineage_digest = edge.lineage_digest
        parent_context_digest = edge.parent_context_digest
        child_context_digest = edge.child_context_digest
        operation_id = edge.operation_id
        operation_kind = edge.operation_kind
        schema_version = CANONICAL_VERSION
        _require_sha256_hex("ContinuityEvidenceRef.lineage_digest", lineage_digest)
        _require_sha256_hex("ContinuityEvidenceRef.parent_context_digest", parent_context_digest)
        _require_sha256_hex("ContinuityEvidenceRef.child_context_digest", child_context_digest)
        _require_non_empty_str("ContinuityEvidenceRef.operation_id", operation_id)
        if type(operation_kind) is not ContextEvolutionKind:
            raise ValueError("ContinuityEvidenceRef.operation_kind must be ContextEvolutionKind")
        object.__setattr__(self, "lineage_digest", lineage_digest)
        object.__setattr__(self, "parent_context_digest", parent_context_digest)
        object.__setattr__(self, "child_context_digest", child_context_digest)
        object.__setattr__(self, "operation_id", operation_id)
        object.__setattr__(self, "operation_kind", operation_kind)
        object.__setattr__(self, "schema_version", schema_version)

    @classmethod
    def from_lineage_edge(cls, edge: ContextLineageEdge) -> "ContinuityEvidenceRef":
        return cls(edge)

    def canonical_bytes(self) -> bytes:
        return (
            _field("evidence.domain", EVIDENCE_DOMAIN_SEPARATOR)
            + _field("evidence.schema_version", self.schema_version)
            + _field("evidence.lineage_digest", self.lineage_digest)
            + _field("evidence.parent_context_digest", self.parent_context_digest)
            + _field("evidence.child_context_digest", self.child_context_digest)
            + _field("evidence.operation_id", self.operation_id)
            + _field("evidence.operation_kind", self.operation_kind.value)
        )


@dataclass(frozen=True)
class ContinuityClaim:
    claim_id: str
    claim_kind: ContinuityClaimKind
    claim_payload: str
    supporting_evidence_refs: tuple[ContinuityEvidenceRef, ...]
    conflict_rule: ContinuityConflictRule = ContinuityConflictRule.APPEND
    target_claim_id: str = "none"
    status: ContinuityClaimStatus = ContinuityClaimStatus.CANDIDATE
    projection_rule_id: str = "dia7-rule-v1"
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("ContinuityClaim.claim_id", self.claim_id)
        object.__setattr__(self, "claim_kind", _require_claim_kind("ContinuityClaim.claim_kind", self.claim_kind))
        _require_non_empty_str("ContinuityClaim.claim_payload", self.claim_payload)
        _require_tuple("ContinuityClaim.supporting_evidence_refs", self.supporting_evidence_refs)
        if not self.supporting_evidence_refs:
            raise ValueError("ContinuityClaim.supporting_evidence_refs must be non-empty")
        if not all(type(ref) is ContinuityEvidenceRef for ref in self.supporting_evidence_refs):
            raise ValueError("ContinuityClaim.supporting_evidence_refs must contain ContinuityEvidenceRef only")
        _reject_duplicate_evidence_refs("ContinuityClaim.supporting_evidence_refs", self.supporting_evidence_refs)
        object.__setattr__(self, "supporting_evidence_refs", tuple(sorted(self.supporting_evidence_refs, key=lambda ref: ref.lineage_digest)))
        object.__setattr__(self, "conflict_rule", _require_conflict_rule("ContinuityClaim.conflict_rule", self.conflict_rule))
        _require_non_empty_str("ContinuityClaim.target_claim_id", self.target_claim_id)
        object.__setattr__(self, "status", _require_claim_status("ContinuityClaim.status", self.status))
        _require_non_empty_str("ContinuityClaim.projection_rule_id", self.projection_rule_id)
        _require_non_empty_str("ContinuityClaim.schema_version", self.schema_version)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("ContinuityClaim.schema_version is frozen")
        if self.status is not ContinuityClaimStatus.CANDIDATE:
            raise ValueError("ContinuityClaim input status must be candidate")
        if self.conflict_rule in (ContinuityConflictRule.SUPERSEDE, ContinuityConflictRule.CORRECT, ContinuityConflictRule.DEPRECATE, ContinuityConflictRule.UNRESOLVED) and self.target_claim_id == "none":
            raise ValueError("ContinuityClaim.target_claim_id is required for non-append conflict rules")
        if self.conflict_rule is ContinuityConflictRule.APPEND and self.target_claim_id != "none":
            raise ValueError("ContinuityClaim.target_claim_id must be none for append claims")

    def with_status(self, status: ContinuityClaimStatus) -> "ProjectedContinuityClaim":
        return ProjectedContinuityClaim.from_claim(self, status)

    def canonical_bytes(self) -> bytes:
        out = (
            _field("claim.domain", CLAIM_DOMAIN_SEPARATOR)
            + _field("claim.schema_version", self.schema_version)
            + _field("claim.id", self.claim_id)
            + _field("claim.kind", self.claim_kind.value)
            + _field("claim.payload", self.claim_payload)
            + _field("claim.conflict_rule", self.conflict_rule.value)
            + _field("claim.target_claim_id", self.target_claim_id)
            + _field("claim.status", self.status.value)
            + _field("claim.projection_rule_id", self.projection_rule_id)
            + _field("claim.evidence_count", str(len(self.supporting_evidence_refs)))
        )
        for ref in self.supporting_evidence_refs:
            out += _field("claim.evidence_ref", ref.canonical_bytes().decode("utf-8"))
        return out


@dataclass(frozen=True, init=False)
class ProjectedContinuityClaim:
    claim_id: str
    claim_kind: ContinuityClaimKind
    claim_payload: str
    supporting_evidence_refs: tuple[ContinuityEvidenceRef, ...]
    conflict_rule: ContinuityConflictRule
    target_claim_id: str
    status: ContinuityClaimStatus
    projection_rule_id: str
    schema_version: str

    def __init__(self, claim: ContinuityClaim, status: ContinuityClaimStatus) -> None:
        if type(claim) is not ContinuityClaim:
            raise ValueError("ProjectedContinuityClaim requires exact ContinuityClaim")
        status = _require_claim_status("ProjectedContinuityClaim.status", status)
        if status is ContinuityClaimStatus.CANDIDATE:
            raise ValueError("ProjectedContinuityClaim.status cannot be candidate")
        object.__setattr__(self, "claim_id", claim.claim_id)
        object.__setattr__(self, "claim_kind", claim.claim_kind)
        object.__setattr__(self, "claim_payload", claim.claim_payload)
        object.__setattr__(self, "supporting_evidence_refs", claim.supporting_evidence_refs)
        object.__setattr__(self, "conflict_rule", claim.conflict_rule)
        object.__setattr__(self, "target_claim_id", claim.target_claim_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "projection_rule_id", claim.projection_rule_id)
        object.__setattr__(self, "schema_version", claim.schema_version)

    @classmethod
    def from_claim(cls, claim: ContinuityClaim, status: ContinuityClaimStatus) -> "ProjectedContinuityClaim":
        return cls(claim, status)

    def canonical_bytes(self) -> bytes:
        out = (
            _field("claim.domain", CLAIM_DOMAIN_SEPARATOR)
            + _field("claim.schema_version", self.schema_version)
            + _field("claim.id", self.claim_id)
            + _field("claim.kind", self.claim_kind.value)
            + _field("claim.payload", self.claim_payload)
            + _field("claim.conflict_rule", self.conflict_rule.value)
            + _field("claim.target_claim_id", self.target_claim_id)
            + _field("claim.status", self.status.value)
            + _field("claim.projection_rule_id", self.projection_rule_id)
            + _field("claim.evidence_count", str(len(self.supporting_evidence_refs)))
        )
        for ref in self.supporting_evidence_refs:
            out += _field("claim.evidence_ref", ref.canonical_bytes().decode("utf-8"))
        return out


@dataclass(frozen=True, init=False)
class ContinuityAnchor:
    anchor_claim: ProjectedContinuityClaim
    anchor_digest: str

    def __init__(self, anchor_claim: ProjectedContinuityClaim) -> None:
        if type(anchor_claim) is not ProjectedContinuityClaim:
            raise ValueError("ContinuityAnchor requires exact ProjectedContinuityClaim")
        if anchor_claim.status is not ContinuityClaimStatus.ACTIVE:
            raise ValueError("ContinuityAnchor requires an active projected claim")
        if anchor_claim.claim_kind is not ContinuityClaimKind.IDENTITY_ANCHOR:
            raise ValueError("ContinuityAnchor requires identity_anchor claim kind")
        object.__setattr__(self, "anchor_claim", anchor_claim)
        object.__setattr__(self, "anchor_digest", _digest_hex(anchor_claim.canonical_bytes()))

    @classmethod
    def from_claim(cls, anchor_claim: ProjectedContinuityClaim) -> "ContinuityAnchor":
        return cls(anchor_claim)

    def canonical_bytes(self) -> bytes:
        return _field("anchor.claim", self.anchor_claim.canonical_bytes().decode("utf-8")) + _field("anchor.digest", self.anchor_digest)


@dataclass(frozen=True)
class ContinuityProjectionPolicy:
    revision: str
    allowed_claim_kinds: tuple[ContinuityClaimKind, ...]
    allowed_conflict_rules: tuple[ContinuityConflictRule, ...]
    min_evidence_refs: int = 1
    projection_algorithm_revision: str = PROJECTION_ALGORITHM_REVISION
    state_digest_algorithm_revision: str = STATE_DIGEST_ALGORITHM_REVISION
    input_canonicalization_revision: str = INPUT_CANONICALIZATION_REVISION
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("ContinuityProjectionPolicy.revision", self.revision)
        _require_tuple("ContinuityProjectionPolicy.allowed_claim_kinds", self.allowed_claim_kinds)
        _require_tuple("ContinuityProjectionPolicy.allowed_conflict_rules", self.allowed_conflict_rules)
        if not self.allowed_claim_kinds:
            raise ValueError("ContinuityProjectionPolicy.allowed_claim_kinds must be non-empty")
        if not self.allowed_conflict_rules:
            raise ValueError("ContinuityProjectionPolicy.allowed_conflict_rules must be non-empty")
        kinds = tuple(_require_claim_kind("ContinuityProjectionPolicy.allowed_claim_kinds", item) for item in self.allowed_claim_kinds)
        rules = tuple(_require_conflict_rule("ContinuityProjectionPolicy.allowed_conflict_rules", item) for item in self.allowed_conflict_rules)
        if len(set(kind.value for kind in kinds)) != len(kinds):
            raise ValueError("ContinuityProjectionPolicy.allowed_claim_kinds must not contain duplicates")
        if len(set(rule.value for rule in rules)) != len(rules):
            raise ValueError("ContinuityProjectionPolicy.allowed_conflict_rules must not contain duplicates")
        object.__setattr__(self, "allowed_claim_kinds", tuple(sorted(kinds, key=lambda item: item.value)))
        object.__setattr__(self, "allowed_conflict_rules", tuple(sorted(rules, key=lambda item: item.value)))
        _require_positive_int("ContinuityProjectionPolicy.min_evidence_refs", self.min_evidence_refs)
        if self.projection_algorithm_revision != PROJECTION_ALGORITHM_REVISION:
            raise ValueError("ContinuityProjectionPolicy.projection_algorithm_revision is not implemented")
        if self.state_digest_algorithm_revision != STATE_DIGEST_ALGORITHM_REVISION:
            raise ValueError("ContinuityProjectionPolicy.state_digest_algorithm_revision is not implemented")
        if self.input_canonicalization_revision != INPUT_CANONICALIZATION_REVISION:
            raise ValueError("ContinuityProjectionPolicy.input_canonicalization_revision is not implemented")
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("ContinuityProjectionPolicy.schema_version is frozen")

    def canonical_bytes(self) -> bytes:
        out = (
            _field("policy.domain", POLICY_DOMAIN_SEPARATOR)
            + _field("policy.schema_version", self.schema_version)
            + _field("policy.revision", self.revision)
            + _field("policy.projection_algorithm_revision", self.projection_algorithm_revision)
            + _field("policy.state_digest_algorithm_revision", self.state_digest_algorithm_revision)
            + _field("policy.input_canonicalization_revision", self.input_canonicalization_revision)
            + _field("policy.min_evidence_refs", str(self.min_evidence_refs))
            + _field("policy.allowed_claim_kind_count", str(len(self.allowed_claim_kinds)))
        )
        for kind in self.allowed_claim_kinds:
            out += _field("policy.allowed_claim_kind", kind.value)
        out += _field("policy.allowed_conflict_rule_count", str(len(self.allowed_conflict_rules)))
        for rule in self.allowed_conflict_rules:
            out += _field("policy.allowed_conflict_rule", rule.value)
        return out

    def policy_fingerprint(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True)
class ContinuityProjectionInput:
    source_graph_revision: str
    source_graph_digest: str
    lineage_edges: tuple[ContextLineageEdge, ...]
    candidate_claims: tuple[ContinuityClaim, ...]
    projection_policy_revision: str
    projection_policy_fingerprint: str
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("ContinuityProjectionInput.source_graph_revision", self.source_graph_revision)
        _require_sha256_hex("ContinuityProjectionInput.source_graph_digest", self.source_graph_digest)
        _require_tuple("ContinuityProjectionInput.lineage_edges", self.lineage_edges)
        if not self.lineage_edges:
            raise ValueError("ContinuityProjectionInput.lineage_edges must be non-empty")
        if not all(type(edge) is ContextLineageEdge for edge in self.lineage_edges):
            raise ValueError("ContinuityProjectionInput.lineage_edges must contain ContextLineageEdge only")
        edges = tuple(sorted(self.lineage_edges, key=lambda edge: edge.lineage_digest))
        if self.lineage_edges != edges:
            raise ValueError("ContinuityProjectionInput.lineage_edges must be canonical sorted order")
        edge_digests = [edge.lineage_digest for edge in edges]
        if len(set(edge_digests)) != len(edge_digests):
            raise ValueError("ContinuityProjectionInput.lineage_edges must not contain duplicates")
        object.__setattr__(self, "lineage_edges", edges)
        _require_tuple("ContinuityProjectionInput.candidate_claims", self.candidate_claims)
        if not all(type(claim) is ContinuityClaim for claim in self.candidate_claims):
            raise ValueError("ContinuityProjectionInput.candidate_claims must contain ContinuityClaim only")
        _reject_duplicate_claim_ids("ContinuityProjectionInput.candidate_claims", self.candidate_claims)
        claims = tuple(sorted(self.candidate_claims, key=lambda claim: claim.claim_id))
        if self.candidate_claims != claims:
            raise ValueError("ContinuityProjectionInput.candidate_claims must be canonical sorted order")
        known_lineage = set(edge_digests)
        for claim in claims:
            for ref in claim.supporting_evidence_refs:
                if ref.lineage_digest not in known_lineage:
                    raise ValueError("ContinuityProjectionInput claim evidence points to missing lineage")
        object.__setattr__(self, "candidate_claims", claims)
        _require_non_empty_str("ContinuityProjectionInput.projection_policy_revision", self.projection_policy_revision)
        _require_sha256_hex("ContinuityProjectionInput.projection_policy_fingerprint", self.projection_policy_fingerprint)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("ContinuityProjectionInput.schema_version is frozen")
        expected_graph_digest = self.compute_graph_digest(edges)
        if self.source_graph_digest != expected_graph_digest:
            raise ValueError("ContinuityProjectionInput.source_graph_digest mismatch")

    @staticmethod
    def compute_graph_digest(lineage_edges: tuple[ContextLineageEdge, ...]) -> str:
        _require_tuple("lineage_edges", lineage_edges)
        if not lineage_edges:
            raise ValueError("lineage_edges must be non-empty")
        if not all(type(edge) is ContextLineageEdge for edge in lineage_edges):
            raise ValueError("lineage_edges must contain ContextLineageEdge only")
        out = _field("input.graph_domain", INPUT_DOMAIN_SEPARATOR) + _field("input.edge_count", str(len(lineage_edges)))
        for edge in sorted(lineage_edges, key=lambda item: item.lineage_digest):
            out += _field("input.edge", edge.semantic_canonical_bytes().decode("utf-8"))
        return _digest_hex(out)

    def canonical_bytes(self) -> bytes:
        out = (
            _field("input.domain", INPUT_DOMAIN_SEPARATOR)
            + _field("input.schema_version", self.schema_version)
            + _field("input.source_graph_revision", self.source_graph_revision)
            + _field("input.source_graph_digest", self.source_graph_digest)
            + _field("input.policy_revision", self.projection_policy_revision)
            + _field("input.policy_fingerprint", self.projection_policy_fingerprint)
            + _field("input.edge_count", str(len(self.lineage_edges)))
        )
        for edge in self.lineage_edges:
            out += _field("input.edge", edge.semantic_canonical_bytes().decode("utf-8"))
        out += _field("input.claim_count", str(len(self.candidate_claims)))
        for claim in self.candidate_claims:
            out += _field("input.claim", claim.canonical_bytes().decode("utf-8"))
        return out


@dataclass(frozen=True, init=False)
class ContinuityState:
    state_schema_version: str
    projection_policy_revision: str
    projection_policy_fingerprint: str
    source_graph_revision: str
    source_graph_digest: str
    active_claims: tuple[ProjectedContinuityClaim, ...]
    unresolved_conflicts: tuple[ProjectedContinuityClaim, ...]
    supporting_lineage_digests: tuple[str, ...]
    continuity_state_digest: str

    def __init__(
        self,
        projection_input: ContinuityProjectionInput,
        policy: ContinuityProjectionPolicy,
        active_claims: tuple[ProjectedContinuityClaim, ...],
        unresolved_conflicts: tuple[ProjectedContinuityClaim, ...],
    ) -> None:
        if type(projection_input) is not ContinuityProjectionInput:
            raise ValueError("ContinuityState requires exact ContinuityProjectionInput")
        if type(policy) is not ContinuityProjectionPolicy:
            raise ValueError("ContinuityState requires exact ContinuityProjectionPolicy")
        _require_tuple("ContinuityState.active_claims", active_claims)
        _require_tuple("ContinuityState.unresolved_conflicts", unresolved_conflicts)
        if not all(type(claim) is ProjectedContinuityClaim for claim in active_claims):
            raise ValueError("ContinuityState.active_claims must contain ProjectedContinuityClaim only")
        if not all(type(claim) is ProjectedContinuityClaim for claim in unresolved_conflicts):
            raise ValueError("ContinuityState.unresolved_conflicts must contain ProjectedContinuityClaim only")
        active = tuple(sorted(active_claims, key=lambda claim: claim.claim_id))
        conflicts = tuple(sorted(unresolved_conflicts, key=lambda claim: claim.claim_id))
        if not all(claim.status is ContinuityClaimStatus.ACTIVE for claim in active):
            raise ValueError("ContinuityState.active_claims must be active")
        if not all(claim.status is ContinuityClaimStatus.CONFLICTED for claim in conflicts):
            raise ValueError("ContinuityState.unresolved_conflicts must be conflicted")
        claim_ids = [claim.claim_id for claim in active + conflicts]
        if len(set(claim_ids)) != len(claim_ids):
            raise ValueError("ContinuityState claims must not contain duplicate ids")
        lineage = sorted({ref.lineage_digest for claim in active + conflicts for ref in claim.supporting_evidence_refs})
        object.__setattr__(self, "state_schema_version", CANONICAL_VERSION)
        object.__setattr__(self, "projection_policy_revision", policy.revision)
        object.__setattr__(self, "projection_policy_fingerprint", policy.policy_fingerprint())
        object.__setattr__(self, "source_graph_revision", projection_input.source_graph_revision)
        object.__setattr__(self, "source_graph_digest", projection_input.source_graph_digest)
        object.__setattr__(self, "active_claims", active)
        object.__setattr__(self, "unresolved_conflicts", conflicts)
        object.__setattr__(self, "supporting_lineage_digests", tuple(lineage))
        object.__setattr__(self, "continuity_state_digest", _digest_hex(self.semantic_canonical_bytes(include_digest=False)))

    def semantic_canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("state.domain", STATE_DOMAIN_SEPARATOR)
            + _field("state.schema_version", self.state_schema_version)
            + _field("state.policy_revision", self.projection_policy_revision)
            + _field("state.policy_fingerprint", self.projection_policy_fingerprint)
            + _field("state.source_graph_revision", self.source_graph_revision)
            + _field("state.source_graph_digest", self.source_graph_digest)
            + _field("state.active_claim_count", str(len(self.active_claims)))
        )
        for claim in self.active_claims:
            out += _field("state.active_claim", claim.canonical_bytes().decode("utf-8"))
        out += _field("state.unresolved_conflict_count", str(len(self.unresolved_conflicts)))
        for claim in self.unresolved_conflicts:
            out += _field("state.unresolved_conflict", claim.canonical_bytes().decode("utf-8"))
        out += _field("state.supporting_lineage_digest_count", str(len(self.supporting_lineage_digests)))
        for digest in self.supporting_lineage_digests:
            out += _field("state.supporting_lineage_digest", digest)
        if include_digest:
            out += _field("state.digest", self.continuity_state_digest)
        return out


@dataclass(frozen=True)
class ContinuityProjectionAudit:
    source_graph_digest: str
    projection_policy_fingerprint: str
    diagnostics: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        _require_sha256_hex("ContinuityProjectionAudit.source_graph_digest", self.source_graph_digest)
        _require_sha256_hex("ContinuityProjectionAudit.projection_policy_fingerprint", self.projection_policy_fingerprint)
        _require_tuple("ContinuityProjectionAudit.diagnostics", self.diagnostics)
        if not all(type(item) is str for item in self.diagnostics):
            raise ValueError("ContinuityProjectionAudit.diagnostics must contain str only")
        _require_non_empty_str("ContinuityProjectionAudit.created_at", self.created_at)


@dataclass(frozen=True, init=False)
class ContinuityProjectionResult:
    continuity_state: ContinuityState
    continuity_state_digest: str
    projection_policy_fingerprint: str
    source_graph_digest: str
    projection_status: str
    rejected_claim_count: int
    unresolved_conflict_count: int
    audit: ContinuityProjectionAudit

    def __init__(self, continuity_state: ContinuityState, audit: ContinuityProjectionAudit, rejected_claim_count: int = 0) -> None:
        if type(continuity_state) is not ContinuityState:
            raise ValueError("ContinuityProjectionResult requires exact ContinuityState")
        if type(audit) is not ContinuityProjectionAudit:
            raise ValueError("ContinuityProjectionResult requires exact ContinuityProjectionAudit")
        if audit.source_graph_digest != continuity_state.source_graph_digest:
            raise ValueError("ContinuityProjectionResult audit graph digest mismatch")
        if audit.projection_policy_fingerprint != continuity_state.projection_policy_fingerprint:
            raise ValueError("ContinuityProjectionResult audit policy fingerprint mismatch")
        if type(rejected_claim_count) is not int or rejected_claim_count < 0:
            raise ValueError("ContinuityProjectionResult.rejected_claim_count must be non-negative int")
        object.__setattr__(self, "continuity_state", continuity_state)
        object.__setattr__(self, "continuity_state_digest", continuity_state.continuity_state_digest)
        object.__setattr__(self, "projection_policy_fingerprint", continuity_state.projection_policy_fingerprint)
        object.__setattr__(self, "source_graph_digest", continuity_state.source_graph_digest)
        object.__setattr__(self, "projection_status", "projected")
        object.__setattr__(self, "rejected_claim_count", rejected_claim_count)
        object.__setattr__(self, "unresolved_conflict_count", len(continuity_state.unresolved_conflicts))
        object.__setattr__(self, "audit", audit)


@runtime_checkable
class ContinuityProjector(Protocol):
    def project(self, projection_input: ContinuityProjectionInput, policy: ContinuityProjectionPolicy, audit: ContinuityProjectionAudit) -> ContinuityProjectionResult:
        ...


class StrictContinuityProjector:
    def project(self, projection_input: ContinuityProjectionInput, policy: ContinuityProjectionPolicy, audit: ContinuityProjectionAudit) -> ContinuityProjectionResult:
        if type(projection_input) is not ContinuityProjectionInput:
            raise ValueError("projection_input must be exact ContinuityProjectionInput")
        if type(policy) is not ContinuityProjectionPolicy:
            raise ValueError("policy must be exact ContinuityProjectionPolicy")
        if type(audit) is not ContinuityProjectionAudit:
            raise ValueError("audit must be exact ContinuityProjectionAudit")
        if projection_input.projection_policy_revision != policy.revision:
            raise ValueError("projection policy revision mismatch")
        if projection_input.projection_policy_fingerprint != policy.policy_fingerprint():
            raise ValueError("projection policy fingerprint mismatch")
        if audit.source_graph_digest != projection_input.source_graph_digest:
            raise ValueError("audit source graph digest mismatch")
        if audit.projection_policy_fingerprint != policy.policy_fingerprint():
            raise ValueError("audit policy fingerprint mismatch")

        active: dict[str, ProjectedContinuityClaim] = {}
        unresolved: dict[str, ProjectedContinuityClaim] = {}
        rejected_count = 0
        all_claim_ids = {claim.claim_id for claim in projection_input.candidate_claims}

        for claim in projection_input.candidate_claims:
            if claim.claim_kind not in policy.allowed_claim_kinds or claim.conflict_rule not in policy.allowed_conflict_rules:
                rejected_count += 1
                continue
            if len(claim.supporting_evidence_refs) < policy.min_evidence_refs:
                rejected_count += 1
                continue
            if claim.conflict_rule is ContinuityConflictRule.APPEND:
                active[claim.claim_id] = claim.with_status(ContinuityClaimStatus.ACTIVE)
                continue
            if claim.target_claim_id not in all_claim_ids:
                raise ValueError("conflict rule target claim does not exist")
            if claim.conflict_rule in (ContinuityConflictRule.SUPERSEDE, ContinuityConflictRule.CORRECT):
                active.pop(claim.target_claim_id, None)
                unresolved.pop(claim.target_claim_id, None)
                active[claim.claim_id] = claim.with_status(ContinuityClaimStatus.ACTIVE)
                continue
            if claim.conflict_rule is ContinuityConflictRule.DEPRECATE:
                active.pop(claim.target_claim_id, None)
                unresolved.pop(claim.target_claim_id, None)
                continue
            if claim.conflict_rule is ContinuityConflictRule.UNRESOLVED:
                target = active.pop(claim.target_claim_id, None)
                if target is not None:
                    unresolved[target.claim_id] = ProjectedContinuityClaim.from_claim(
                        _projected_to_candidate(target), ContinuityClaimStatus.CONFLICTED
                    )
                unresolved[claim.claim_id] = claim.with_status(ContinuityClaimStatus.CONFLICTED)
                continue
            raise ValueError("unsupported conflict rule")

        state = ContinuityState(projection_input, policy, tuple(active.values()), tuple(unresolved.values()))
        return ContinuityProjectionResult(state, audit, rejected_count)


def _projected_to_candidate(projected: ProjectedContinuityClaim) -> ContinuityClaim:
    return ContinuityClaim(
        projected.claim_id,
        projected.claim_kind,
        projected.claim_payload,
        projected.supporting_evidence_refs,
        projected.conflict_rule,
        projected.target_claim_id,
        ContinuityClaimStatus.CANDIDATE,
        projected.projection_rule_id,
        projected.schema_version,
    )
