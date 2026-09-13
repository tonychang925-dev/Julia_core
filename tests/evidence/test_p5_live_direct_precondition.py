from __future__ import annotations

import json
from pathlib import Path
from typing import get_type_hints

from julia_core.context_admission import ExclusiveAdmissionRequest
from julia_core.projection.contracts import IdentityFrameSet


REPOSITORY = Path(__file__).resolve().parents[2]
RUN_PATH = REPOSITORY / "artifacts/continuity/P5_C_REAL_GOLDEN_MIRA_CANARY_RUN_V1.json"
PREFLIGHT_PATH = REPOSITORY / "artifacts/continuity/P5_C_REAL_CANARY_PREFLIGHT_V1.json"


def test_p5_live_block_is_preserved_and_identity_carrier_defect_is_corrected() -> None:
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    identity_hints = get_type_hints(ExclusiveAdmissionRequest)["identity_frames"]
    required_identities = preflight["canonical_input"]["identity_refs"]

    assert len(required_identities) == 3
    assert identity_hints == (IdentityFrameSet | None)
    assert run["pre_provider_gate"]["failure"] == {
        "code": "C03_IDENTITY_FRAME_CARDINALITY_MISMATCH",
        "message": (
            "ExclusiveAdmissionRequest admits exactly one IdentityFrame and "
            "EvidenceOnlyCanonicalExecutionObserver binds exactly one identity_frame, "
            "but P5-C requires all three exact admitted Identity refs to pass through "
            "the sealed C03 path."
        ),
        "remaining_positions": 2,
        "forbidden_repairs": [
            "select only one admitted Identity and silently discard the other two",
            "construct an unadmitted composite IdentityFrame",
            "mutate C03/runtime/provider production semantics during P5-LIVE",
            "place Identity records outside the sealed C03 path",
        ],
    }
    assert run["execution"]["provider_call_count"] == 0
    assert run["final_result"] == "BLOCKED_BY_DIRECT_CANARY_PRECONDITION"


def test_p5_live_block_preserves_zero_authority_and_honest_evaluation() -> None:
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))

    assert run["pre_provider_gate"]["provider_call_started"] is False
    assert run["execution"]["retries"] == 0
    assert run["evaluation"]["global_disposition"] == "INCONCLUSIVE"
    assert all(
        value == "INCONCLUSIVE_NOT_EVALUATED_NO_PROVIDER_OUTPUT"
        for key, value in run["evaluation"].items()
        if key != "global_disposition"
    )
    assert all(value == 0 for value in run["authority"].values())
