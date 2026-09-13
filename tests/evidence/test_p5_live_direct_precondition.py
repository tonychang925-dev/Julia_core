from __future__ import annotations

import json
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
RUN_PATH = REPOSITORY / "artifacts/continuity/P5_C_REAL_GOLDEN_MIRA_CANARY_RUN_V1.json"
PREFLIGHT_PATH = REPOSITORY / "artifacts/continuity/P5_C_REAL_CANARY_PREFLIGHT_V1.json"


def test_p5_live_real_canary_binds_pinned_preflight_and_exact_inputs() -> None:
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))

    assert run["preflight_head"] == "e2a3a30d56b2c50a35f5498dc9a9ce2ee3a8f5c0"
    assert run["preflight_artifact_blob"] == "2f0da6df7560348198b842301bf272e2e033433d"
    assert run["preflight_digest"] == preflight["preflight_digest"]
    assert run["corrected_seam_head"] == "2596ac93c2b5d9b0468136a37cef171a0266fa28"
    assert (
        run["corrected_seam_artifact_blob"]
        == "f1b66957814a97a16b332250b1b8bfda2d72e1d2"
    )
    assert run["canonical_input"]["identity_carrier"] == "IdentityFrameSet"
    assert run["canonical_input"]["identity_refs"] == [
        item["ref"] for item in preflight["canonical_input"]["identity_refs"]
    ]
    assert run["canonical_input"]["ordered_memory_experience_refs"] == [
        item["ref"]
        for item in preflight["canonical_input"]["ordered_memory_experience_refs"]
    ]
    assert run["cue"] == "Hi Mira，还记得我吗？"


def test_p5_live_real_canary_has_one_successful_call_and_pass_evaluation() -> None:
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    evaluation = run["p5_d_evaluation_record"]

    assert run["execution"]["provider_call_count"] == 1
    assert run["execution"]["retries"] == 0
    assert run["execution"]["observer_disposition"] == "SUCCEEDED"
    assert run["execution"]["output_present"] is True
    assert len(evaluation["dimensions"]) == 9
    assert all(item["disposition"] == "PASS" for item in evaluation["dimensions"])
    assert evaluation["global_disposition"] == "PASS"
    assert all(value == 0 for value in run["authority"].values())
    assert run["final_result"] == "PASS_REAL_GOLDEN_MIRA_CANARY"
