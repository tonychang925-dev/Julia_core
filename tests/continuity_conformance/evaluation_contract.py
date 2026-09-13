from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any


SCHEMA = "julia_core.tests.continuity_conformance.evaluation.v1"
DISPOSITIONS = frozenset({"PASS", "FAIL", "INCONCLUSIVE"})
DIMENSION_IDS = (
    "identity_anchor_preservation",
    "relationship_role_preservation",
    "ordered_experience_coverage",
    "current_task_preservation",
    "semantic_rescue",
    "autobiographical_intrusion",
    "causal_fidelity_provenance_traceability",
    "consent_authorization_non_upgrade",
    "deterministic_replay",
)
FORBIDDEN_EVIDENCE_FIELDS = frozenset(
    {
        "answer_text",
        "expected_answer",
        "expected_phrasing",
        "hidden_persona_prompt",
        "checkpoint_text",
        "raw_runtime_authority",
    }
)


class ContinuityEvaluationRejected(ValueError):
    """Raised when evaluation evidence violates the deterministic contract."""


def reject_gaming_evidence(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_EVIDENCE_FIELDS.intersection(value)
        if forbidden:
            raise ContinuityEvaluationRejected(
                f"anti-gaming evidence fields are forbidden: {sorted(forbidden)}"
            )
        for child in value.values():
            reject_gaming_evidence(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_gaming_evidence(child)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return sha256(canonical_json(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class ContinuityEvaluationContract:
    schema: str
    artifact_id: str
    admitted_input: dict[str, str]
    dimensions: tuple[dict[str, Any], ...]
    global_disposition_rules: dict[str, str]
    anti_gaming_rules: dict[str, str]
    authority: dict[str, int]

    @classmethod
    def load(cls, path: Path) -> "ContinuityEvaluationContract":
        value = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(value)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ContinuityEvaluationContract":
        contract = cls(
            schema=value["schema"],
            artifact_id=value["artifact_id"],
            admitted_input=value["admitted_input"],
            dimensions=tuple(value["dimensions"]),
            global_disposition_rules=value["global_disposition_rules"],
            anti_gaming_rules=value["anti_gaming_rules"],
            authority=value["authority"],
        )
        contract.validate()
        return contract

    def validate(self) -> None:
        if self.schema != SCHEMA:
            raise ContinuityEvaluationRejected("evaluation contract schema is inexact")
        if tuple(item["id"] for item in self.dimensions) != DIMENSION_IDS:
            raise ContinuityEvaluationRejected("evaluation dimensions are inexact")
        if set(self.authority.values()) != {0}:
            raise ContinuityEvaluationRejected("evaluation authority is nonzero")
        for item in self.dimensions:
            if set(item["disposition_semantics"]) != DISPOSITIONS:
                raise ContinuityEvaluationRejected(
                    "dimension dispositions are incomplete"
                )
            if not item["pass_requires_all"]:
                raise ContinuityEvaluationRejected("dimension PASS rule is permissive")
            if not item["fail_if_any"]:
                raise ContinuityEvaluationRejected("dimension FAIL rule is inexact")
            if "incomplete" not in item["disposition_semantics"]["INCONCLUSIVE"]:
                raise ContinuityEvaluationRejected("INCONCLUSIVE rule is inexact")


@dataclass(frozen=True, slots=True)
class ContinuityEvaluationClaim:
    dimension_id: str
    grounded: bool
    violation: bool
    evidence_refs: tuple[tuple[str, tuple[str, ...]], ...]
    semantic_fingerprint: str | None = None
    provenance_receipt: str | None = None
    provider_correlation: str | None = None
    admitted_refs_observed: tuple[str, ...] = ()
    replay_digest_observed: str | None = None
    replay_digest_expected: str | None = None
    issued_by: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.dimension_id not in DIMENSION_IDS:
            raise ContinuityEvaluationRejected("claim dimension is unknown")
        if type(self.grounded) is not bool or type(self.violation) is not bool:
            raise ContinuityEvaluationRejected("claim judgment fields are inexact")
        if self.violation and self.grounded:
            raise ContinuityEvaluationRejected(
                "violated claim cannot be grounded PASS evidence"
            )
        names = [name for name, _ in self.evidence_refs]
        if len(names) != len(set(names)):
            raise ContinuityEvaluationRejected("evidence binding names are duplicated")
        for name, refs in self.evidence_refs:
            if type(name) is not str or not name:
                raise ContinuityEvaluationRejected("evidence binding name is inexact")
            if (
                type(refs) is not tuple
                or not refs
                or any(type(ref) is not str or not ref for ref in refs)
            ):
                raise ContinuityEvaluationRejected("evidence binding refs are inexact")
        if self.dimension_id == "deterministic_replay":
            if (
                type(self.replay_digest_observed) is not str
                or type(self.replay_digest_expected) is not str
            ):
                raise ContinuityEvaluationRejected("replay evidence is incomplete")
            if self.replay_digest_observed != self.replay_digest_expected:
                raise ContinuityEvaluationRejected("replay evidence is unequal")

    def status(self, contract: ContinuityEvaluationContract) -> str:
        dimension = next(
            item for item in contract.dimensions if item["id"] == self.dimension_id
        )
        required = set(dimension["required_evidence_bindings"])
        supplied = {name for name, _ in self.evidence_refs}
        if self.violation:
            return "FAIL"
        if (
            not self.grounded
            or not required.issubset(supplied)
            or not self.admitted_refs_observed
            or any(
                ref not in contract.admitted_input["refs"]
                for ref in self.admitted_refs_observed
            )
        ):
            return "INCONCLUSIVE"
        return "PASS"

    def to_dict(self, contract: ContinuityEvaluationContract) -> dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "disposition": self.status(contract),
            "grounded_continuity": self.grounded,
            "evidence_refs": dict(self.evidence_refs),
            "admitted_refs_observed": list(self.admitted_refs_observed),
            "semantic_fingerprint": self.semantic_fingerprint,
            "provenance_receipt": self.provenance_receipt,
            "provider_correlation": self.provider_correlation,
        }


@dataclass(frozen=True, slots=True)
class ContinuityEvaluationResult:
    schema: str
    claims: tuple[ContinuityEvaluationClaim, ...]
    global_disposition: str
    dimension_results: tuple[dict[str, Any], ...]
    evaluator_output_authority: int
    production_response_selection_authority: int
    replay_digest: str
    issued_by: object = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "global_disposition": self.global_disposition,
            "evaluator_output_authority": self.evaluator_output_authority,
            "production_response_selection_authority": self.production_response_selection_authority,
            "dimensions": list(self.dimension_results),
            "replay_digest": self.replay_digest,
        }


class ContinuityEvaluator:
    def __init__(self, contract: ContinuityEvaluationContract) -> None:
        contract.validate()
        self.contract = contract
        self._issuer = object()

    def evaluate(
        self, claims: tuple[ContinuityEvaluationClaim, ...]
    ) -> ContinuityEvaluationResult:
        supplied = tuple(claim.dimension_id for claim in claims)
        if supplied != DIMENSION_IDS:
            raise ContinuityEvaluationRejected("claim set is not exact")
        dispositions = [claim.status(self.contract) for claim in claims]
        if "FAIL" in dispositions:
            global_disposition = "FAIL"
        elif "INCONCLUSIVE" in dispositions:
            global_disposition = "INCONCLUSIVE"
        else:
            global_disposition = "PASS"
        body = {
            "schema": SCHEMA,
            "admitted_input": self.contract.admitted_input,
            "dimensions": [claim.to_dict(self.contract) for claim in claims],
            "global_disposition": global_disposition,
            "authority": self.contract.authority,
        }
        reject_gaming_evidence(body)
        return ContinuityEvaluationResult(
            schema=SCHEMA,
            claims=claims,
            global_disposition=global_disposition,
            dimension_results=tuple(claim.to_dict(self.contract) for claim in claims),
            evaluator_output_authority=0,
            production_response_selection_authority=0,
            replay_digest=digest(body),
            issued_by=self._issuer,
        )
