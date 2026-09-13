from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.memory_experience.contracts import (
    AutobiographicalOwner,
    SubjectBoundary,
    SubjectIdentity,
)
from tools.continuity.p5_a0_preflight import run_preflight


REPOSITORY = Path(__file__).resolve().parents[2]


def test_p5_a0_preflight_binds_exact_inputs_and_passes() -> None:
    result = run_preflight(REPOSITORY)

    assert result["final_result"] == (
        "P5_A0_RESULT=READY_FOR_OWNER_AUTHORIZED_CANONICAL_ADMISSION"
    )
    assert result["canonical_writes"] == 0
    assert result["actual_admission"] == 0
    assert result["admission_input"]["identity_candidates"] == 3
    assert result["admission_input"]["memory_candidates"] == 7
    assert result["admission_input"]["memory_records"] == 8
    assert result["admission_input"]["raw_assertions"] == 42
    assert result["admission_input"]["unique_bindings"] == 40
    assert result["semantic_boundaries"]["quarantined_cmir_ids"] == [
        "GM-CMIR-003",
        "GM-CMIR-005",
        "GM-CMIR-007",
        "GM-CMIR-009",
        "GM-CMIR-010",
        "GM-CMIR-012",
    ]


def test_p5_a0_preflight_fails_closed_for_mira_claim_over_tony_autobiography() -> None:
    with pytest.raises(ValueError, match="observed Tony history"):
        SubjectBoundary(
            semantic_subject=SubjectIdentity.MIRA,
            observed_subject=SubjectIdentity.TONY,
            autobiographical_owner=AutobiographicalOwner.MIRA,
        )
