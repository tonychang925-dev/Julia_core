from __future__ import annotations

import json
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
OBSERVATION = REPOSITORY / "artifacts/continuity/P6_C_POST_CUTOVER_OBSERVATION_V1.json"
P6_B = REPOSITORY / "artifacts/continuity/P6_B_CONTROLLED_CUTOVER_EXECUTION_V1.json"


def observation() -> dict[str, object]:
    return json.loads(OBSERVATION.read_text(encoding="utf-8"))


def test_p6_c_observes_pinned_main_ruleset_and_p6_b_binding() -> None:
    active = observation()
    p6_b = json.loads(P6_B.read_text(encoding="utf-8"))

    assert active["remote_main_observation"]["observed_head"] == (
        "28b502ca4f48e580d4941e095bb8dccc6f3e9682"
    )
    assert active["ruleset_observation"]["enforcement"] == "active"
    assert active["ruleset_observation"]["required_status_check"] == (
        "NO_CRITICAL_FALLBACK_GATE"
    )
    assert active["ruleset_observation"]["bypass_actors"] == []
    assert active["ruleset_observation"]["current_user_can_bypass"] == "never"
    assert active["p6_b_binding"]["result"] == p6_b["final_result"]
    assert (
        active["p6_b_binding"]["evidence_blob"]
        == "9c3650ec52603c47ee27eac2d756861035e3806a"
    )


def test_p6_c_observes_continuity_provenance_and_regression() -> None:
    active = observation()

    assert active["continuity_smoke"]["identity_count"] == 3
    assert active["continuity_smoke"]["ordered_memory_experience_count"] == 8
    assert active["continuity_smoke"]["sealed_contract"] == (
        "julia_core.context_admission.c03.production.v3"
    )
    assert active["provider_observer_provenance"]["correlation_consistent"] is True
    assert (
        active["provider_observer_provenance"]["semantic_fingerprint_consistent"]
        is True
    )
    assert active["provider_observer_provenance"]["gate_receipt_consistent"] is True
    assert active["no_authority_degradation"]["result"] == "PASS"
    assert active["frozen_regression_subset"]["result"].startswith("PASS: 242 passed")


def test_p6_c_does_not_recommend_rollback_without_trigger() -> None:
    active = observation()

    assert all(
        item["status"] == "NOT_TRIGGERED"
        for item in active["rollback_trigger_evaluation"]
    )
    assert active["rollback_recommendation"] == "NOT_RECOMMENDED"
    assert all(value == 0 for value in active["authority"].values())
    assert active["blockers"] == []
    assert active["final_result"] == "PASS_P6_C_POST_CUTOVER_OBSERVATION"
