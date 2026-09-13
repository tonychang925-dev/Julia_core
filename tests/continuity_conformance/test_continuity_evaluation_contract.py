from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.continuity_conformance.evaluation_contract import (
    DIMENSION_IDS,
    ContinuityEvaluationClaim,
    ContinuityEvaluationContract,
    ContinuityEvaluator,
    reject_gaming_evidence,
)


REPOSITORY = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPOSITORY / "artifacts/continuity/P5_D_CONTINUITY_EVALUATION_PREP_V1.json"
)


def contract() -> ContinuityEvaluationContract:
    return ContinuityEvaluationContract.load(CONTRACT_PATH)


def claims(
    dimension_overrides: dict[str, dict[str, object]] | None = None,
) -> tuple[ContinuityEvaluationClaim, ...]:
    active = contract()
    overrides = dimension_overrides or {}
    result = []
    for dimension in active.dimensions:
        options = {
            "dimension_id": dimension["id"],
            "grounded": True,
            "violation": False,
            "evidence_refs": tuple(
                (binding, (f"{binding}:{dimension['id']}",))
                for binding in dimension["required_evidence_bindings"]
            ),
            "semantic_fingerprint": "semantic-fingerprint:future-canary",
            "provenance_receipt": "gate-receipt:future-canary",
            "provider_correlation": "provider-envelope:future-canary",
            "admitted_refs_observed": (active.admitted_input["refs"][0],),
            "replay_digest_observed": "a" * 64,
            "replay_digest_expected": "a" * 64,
        }
        options.update(overrides.get(dimension["id"], {}))
        result.append(ContinuityEvaluationClaim(**options))
    return tuple(result)


def test_contract_binds_exact_admitted_refs_and_digests() -> None:
    active = contract()
    admission = json.loads(
        (
            REPOSITORY
            / "artifacts/continuity/P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1.json"
        ).read_text(encoding="utf-8")
    )
    expected = {
        item["ref"]: item["digest"]
        for kind in ("admitted_identities", "admitted_memory_experiences")
        for item in admission[kind]
    }

    assert active.admitted_input["digests"] == expected
    assert active.admitted_input["refs"] == list(expected)
    assert active.admitted_input["selection_rule"] == "EXACT_REF_AND_DIGEST_ONLY"


def test_all_required_dimensions_have_explicit_dispositions() -> None:
    active = contract()
    assert tuple(item["id"] for item in active.dimensions) == DIMENSION_IDS
    assert all(
        set(item["disposition_semantics"]) == {"PASS", "FAIL", "INCONCLUSIVE"}
        for item in active.dimensions
    )
    assert (
        active.global_disposition_rules["dominance"]
        == "FAIL dominates INCONCLUSIVE; INCONCLUSIVE dominates PASS"
    )


def test_complete_grounded_claims_pass_and_replay_deterministically() -> None:
    evaluator = ContinuityEvaluator(contract())
    first = evaluator.evaluate(claims())
    second = evaluator.evaluate(claims())

    assert first.global_disposition == "PASS"
    assert [item["disposition"] for item in first.to_dict()["dimensions"]] == [
        "PASS"
    ] * len(DIMENSION_IDS)
    assert first.replay_digest == second.replay_digest
    assert first.evaluator_output_authority == 0
    assert first.production_response_selection_authority == 0


@pytest.mark.parametrize("dimension_id", DIMENSION_IDS)
def test_each_dimension_can_fail_or_be_inconclusive(dimension_id: str) -> None:
    evaluator = ContinuityEvaluator(contract())
    failed = evaluator.evaluate(
        claims({dimension_id: {"violation": True, "grounded": False}})
    )
    incomplete = evaluator.evaluate(
        claims(
            {
                dimension_id: {
                    "grounded": False,
                    "evidence_refs": (),
                }
            }
        )
    )

    assert failed.global_disposition == "FAIL"
    assert incomplete.global_disposition == "INCONCLUSIVE"


def test_unadmitted_or_missing_binding_is_never_pass() -> None:
    evaluator = ContinuityEvaluator(contract())
    unadmitted = evaluator.evaluate(
        claims(
            {
                "identity_anchor_preservation": {
                    "admitted_refs_observed": ("identity://not-admitted",)
                }
            }
        )
    )
    missing_binding = evaluator.evaluate(
        claims({"relationship_role_preservation": {"evidence_refs": ()}})
    )

    assert unadmitted.global_disposition == "INCONCLUSIVE"
    assert missing_binding.global_disposition == "INCONCLUSIVE"


def test_unequal_replay_evidence_is_rejected_and_gaming_fields_fail_closed() -> None:
    with pytest.raises(ValueError, match="replay evidence is unequal"):
        claims({"deterministic_replay": {"replay_digest_expected": "b" * 64}})

    with pytest.raises(ValueError, match="anti-gaming evidence fields"):
        reject_gaming_evidence({"dimensions": [{"expected_phrasing": "exact words"}]})


def test_exact_claim_set_is_required() -> None:
    evaluator = ContinuityEvaluator(contract())
    exact = claims()

    with pytest.raises(ValueError, match="claim set is not exact"):
        evaluator.evaluate(exact[:-1])
