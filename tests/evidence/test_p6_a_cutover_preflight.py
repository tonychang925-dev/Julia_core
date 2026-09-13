from __future__ import annotations

import json
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
PREFLIGHT = REPOSITORY / "artifacts/continuity/P6_A_CUTOVER_PREFLIGHT_V1.json"
P5_RUN = REPOSITORY / "artifacts/continuity/P5_C_REAL_GOLDEN_MIRA_CANARY_RUN_V1.json"


def artifact() -> dict[str, object]:
    return json.loads(PREFLIGHT.read_text(encoding="utf-8"))


def test_p6_a_binds_exact_remote_graph_and_frozen_candidate() -> None:
    active = artifact()

    assert active["remote_verification"]["main"]["observed_head"] == (
        "e2edba9dfff460e3769f93b58491afaf644e6da5"
    )
    assert active["remote_verification"]["frozen_candidate"]["observed_head"] == (
        "28b502ca4f48e580d4941e095bb8dccc6f3e9682"
    )
    assert active["git_graph"]["merge_base"] == (
        "e2edba9dfff460e3769f93b58491afaf644e6da5"
    )
    assert active["git_graph"]["merge_base_equals_main"] is True
    assert active["git_graph"]["ahead_by"] == 72
    assert active["git_graph"]["behind_by"] == 0
    assert active["git_graph"]["proposed_cutover_head"] == (
        "28b502ca4f48e580d4941e095bb8dccc6f3e9682"
    )
    assert (
        active["git_graph"][
            "pending_drift_between_p5_candidate_and_proposed_cutover_head"
        ]
        == 0
    )


def test_p6_a_binds_frozen_p5_run_and_required_evidence() -> None:
    active = artifact()
    run = json.loads(P5_RUN.read_text(encoding="utf-8"))
    verification = active["p5_run_verification"]

    assert verification["remote_git_blob"] == "6498bad21a580fda73a601d0c9d4f84ba179c825"
    assert verification["remote_readback_verified"] is True
    assert verification["final_result"] == run["final_result"]
    assert (
        verification["provider_call_count"] == run["execution"]["provider_call_count"]
    )
    assert verification["retries"] == run["execution"]["retries"]
    assert verification["p5_d_evaluation"] == (
        run["p5_d_evaluation_record"]["global_disposition"]
    )
    assert len(active["required_evidence_bindings"]) == 6
    assert all(
        item["remote_readback_verified"] is True
        for item in active["required_evidence_bindings"]
    )


def test_p6_a_requires_no_mutation_and_defines_future_contracts() -> None:
    active = artifact()

    assert all(
        item["result"] == "PASS"
        for item in active["cutover_readiness_checks"].values()
        if isinstance(item, dict) and "result" in item
    )
    assert active["rollback_contract"]["execution_status"] == "PLANNED_NOT_EXECUTED"
    assert active["rollback_contract"]["rollback_target"]["git_target"] == (
        "e2edba9dfff460e3769f93b58491afaf644e6da5"
    )
    assert len(active["rollback_contract"]["triggers"]) == 6
    assert active["post_cutover_observation_contract"]["execution_status"] == (
        "PLANNED_NOT_EXECUTED"
    )
    assert len(active["post_cutover_observation_contract"]["checks"]) == 6
    assert all(value == 0 for value in active["authority"].values())
    assert active["blockers"] == []
    assert active["final_result"] == "PASS_READY_FOR_P6_B_OWNER_GATE"
