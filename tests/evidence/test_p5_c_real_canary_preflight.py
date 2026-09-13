from __future__ import annotations

import json
import subprocess
from hashlib import sha256
from copy import deepcopy
from pathlib import Path

import pytest

from tests.continuity_conformance.evaluation_contract import (
    DIMENSION_IDS,
    ContinuityEvaluationContract,
)


REPOSITORY = Path(__file__).resolve().parents[2]
ARTIFACT = REPOSITORY / "artifacts/continuity/P5_C_REAL_CANARY_PREFLIGHT_V1.json"
P5_B = (
    REPOSITORY
    / "artifacts/continuity/P5_B_POST_ADMISSION_CANONICAL_VERIFICATION_V1.json"
)
P5_D = REPOSITORY / "artifacts/continuity/P5_D_CONTINUITY_EVALUATION_PREP_V1.json"
CUE = "Hi Mira，还记得我吗？"


def artifact() -> dict[str, object]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def git_blob(path: str) -> str:
    return subprocess.run(
        ["git", "ls-tree", "HEAD", path],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[2]


def canonical_binding(source: dict[str, object]) -> tuple[list[dict], list[dict]]:
    state = source["canonical_state"]
    return state["identity_refs"], state["memory_experience_refs"]


def test_preflight_binds_exact_p5_b_canonical_input() -> None:
    active = artifact()
    p5_b = json.loads(P5_B.read_text(encoding="utf-8"))
    identities, memories = canonical_binding(p5_b)
    expected_identities = [
        {
            "order": index + 1,
            "ref": item["ref"],
            "digest": item["digest"],
            "lifecycle_status": item["status"],
        }
        for index, item in enumerate(identities)
    ]
    expected_memories = [
        {
            "order": index + 1,
            "ref": item["ref"],
            "digest": item["digest"],
            "lifecycle_status": item["status"],
        }
        for index, item in enumerate(memories)
    ]

    assert active["canonical_input"]["identity_refs"] == expected_identities
    assert (
        active["canonical_input"]["ordered_memory_experience_refs"] == expected_memories
    )
    assert active["dependency"]["p5_b_remote_head"] == (
        "09f6e753004b4e509a4da217508a8b5e2c7417ee"
    )
    assert (
        git_blob(
            "artifacts/continuity/P5_B_POST_ADMISSION_CANONICAL_VERIFICATION_V1.json"
        )
        == active["dependency"]["p5_b_artifact_blob"]
    )


def test_preflight_binds_exact_cue_and_no_phrase_authority() -> None:
    cue = artifact()["canary_cue"]

    assert cue["text"] == CUE
    assert cue["byte_encoding"] == "UTF-8"
    assert cue["normalization"] == "NONE"
    assert cue["phrase_matching_authority"] == 0


def test_preflight_reuses_p5_d_contract_without_new_subsystem() -> None:
    active = artifact()
    contract = ContinuityEvaluationContract.load(P5_D)
    evaluation = active["evaluation_binding"]

    assert tuple(evaluation["dimensions"]) == DIMENSION_IDS
    assert all(value == 0 for value in contract.authority.values())
    assert evaluation["contract_artifact_blob"] == git_blob(
        "artifacts/continuity/P5_D_CONTINUITY_EVALUATION_PREP_V1.json"
    )
    assert evaluation["contract_module_blob"] == git_blob(
        "tests/continuity_conformance/evaluation_contract.py"
    )
    assert evaluation["new_evaluation_subsystem"] == 0
    assert "semantic_rescue_definition" in evaluation
    assert "autobiographical_intrusion_definition" in evaluation


def test_preflight_reuses_exact_p4_observer_and_comparison_surfaces() -> None:
    reused = artifact()["reused_p4_surfaces"]

    assert reused["observer_blob"] == git_blob("julia_core/execution_observer.py")
    assert reused["comparison_blob"] == git_blob("julia_core/comparison.py")
    assert reused["observer_schema"] == (
        "julia_core.evidence.canonical_execution_observer.v1"
    )
    assert reused["comparison_schema"] == "julia_core.evidence.side_by_side.v1"


def test_provider_call_never_occurs_before_all_fail_closed_gates() -> None:
    active = artifact()
    gates = active["pre_provider_fail_closed_gates"]

    assert gates["behavior"] == "STOP_BEFORE_PROVIDER_CALL"
    assert len(gates["checks"]) == 12
    assert gates["fallback_provider"] == 0
    assert gates["default_or_latest_selection"] == 0
    assert active["execution_isolation"] == {
        "live_model_call": 0,
        "real_canary_execution": 0,
        "canonical_writes": 0,
        "new_admission": 0,
        "provider_runtime_semantic_mutation": 0,
        "production_response_switching": 0,
        "p6_work": 0,
        "new_evaluation_subsystem": 0,
        "new_p5_f_g_h_node": 0,
    }


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("ref", "identity://not-admitted"),
        ("digest", "0" * 64),
        ("lifecycle_status", "CANDIDATE"),
    ],
)
def test_mechanical_preflight_rejects_invalid_canonical_binding(
    field: str, invalid: str
) -> None:
    active = artifact()
    p5_b = json.loads(P5_B.read_text(encoding="utf-8"))
    current = active["canonical_input"]["identity_refs"]
    expected = deepcopy(current)
    current[0][field] = invalid

    with pytest.raises(AssertionError):
        assert current == expected


def test_run_record_contract_has_exact_correlation_and_evidence_fields() -> None:
    run = artifact()["future_run_contract"]

    assert run["run_record_schema"] == (
        "julia_core.continuity.p5_c.real_golden_mira_canary_run.v1"
    )
    assert run["run_record_path"] == (
        "artifacts/continuity/P5_C_REAL_GOLDEN_MIRA_CANARY_RUN_V1.json"
    )
    assert run["preflight_correlation_id"] == (
        "p5-c-real-canary-preflight:golden-mira:resurrection-alpha:v1"
    )
    assert "preflight_digest" in run["required_fields"]
    assert run["canary_output_authority"] == 0
    assert run["production_response_selection_authority"] == 0
    assert artifact()["final_result"] == "PASS_READY_FOR_REAL_GOLDEN_MIRA_CANARY"


def test_preflight_digest_recomputes_from_exact_bound_surfaces() -> None:
    active = artifact()
    value = {
        "canonical_input": active["canonical_input"],
        "cue": active["canary_cue"],
        "dimensions": active["evaluation_binding"]["dimensions"],
        "observer_blob": active["reused_p4_surfaces"]["observer_blob"],
        "comparison_blob": active["reused_p4_surfaces"]["comparison_blob"],
        "fail_closed_checks": active["pre_provider_fail_closed_gates"]["checks"],
    }
    serialized = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    assert active["preflight_digest"] == sha256(serialized).hexdigest()
