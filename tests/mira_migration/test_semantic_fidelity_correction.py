from __future__ import annotations

import copy

import pytest

from tools.mira_migration.semantic_fidelity_correction import (
    SemanticFidelityCorrectionError,
    build_successor,
)


RAW_SHA = "a" * 64
OLD_DIGEST = "b" * 64


def preview() -> dict:
    return {
        "memory_experience_previews": [
            {
                "candidate_id": "CAND-1",
                "chain_id": "CHAIN-1",
                "canonical_preview": {
                    "digest": OLD_DIGEST,
                    "payload": {
                        "schema": "julia_core.memory_experience.record.v1",
                        "experience_id": "golden-mira:CHAIN-1",
                        "version_id": "v1",
                        "experience_type": "NarrativeExperience",
                        "content": {
                            "event": "His sister arrived.",
                            "meaning_at_time": "He was not alone.",
                            "significance": "Care mattered.",
                            "later_reinterpretation": "His sister's care changed the frame.",
                            "source_refs": ["raw://chain/1"],
                        },
                        "provenance_refs": [
                            {
                                "source_type": "old-source",
                                "source_ref": "raw://binding/1",
                                "source_digest": "c" * 64,
                                "admission_metadata": {"binding_id": "B1"},
                            }
                        ],
                        "created_at": "raw-create-time:1",
                        "predecessor_version_id": None,
                        "authority": {
                            "standing_authorization": False,
                            "current_consent": False,
                            "mutates_identity": False,
                            "runtime_authority": False,
                        },
                    },
                },
            }
        ]
    }


def raw_export() -> dict:
    return {
        "mapping": {
            "m1": {
                "message": {
                    "content": {"parts": ["姐姐当天就来了。"]},
                }
            }
        }
    }


def manifest() -> dict:
    import hashlib

    body = "姐姐当天就来了。"
    text_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return {
        "schema": "julia_core.mira_migration.semantic_fidelity_manifest.v1",
        "artifact_id": "SF-CORRECTION-1",
        "task_id": "TASK-1",
        "status": "PREP_ONLY",
        "raw_export": {"sha256": RAW_SHA},
        "historical_candidate": {
            "preview_commit": "d" * 40,
            "preview_path": "artifact.json",
            "candidate_id": "CAND-1",
            "canonical_ref": "memory-experience://golden-mira:CHAIN-1/v1",
            "version_id": "v1",
            "canonical_digest": OLD_DIGEST,
        },
        "successor": {
            "candidate_id": "CAND-1-SF1",
            "proposed_version_id": "v2-semantic-fidelity-preview",
        },
        "corrections": [
            {
                "correction_id": "CORR-1",
                "target_path": ["content", "event"],
                "source_semantic_attribute": {
                    "dimension": "kinship.sibling_relative_age",
                    "value": "OLDER",
                },
                "normalized_semantic_attribute": {
                    "dimension": "kinship.sibling_relative_age",
                    "value": "OLDER",
                },
                "old_normalized_span": "sister",
                "corrected_normalized_span": "older sister",
                "raw_evidence": [
                    {
                        "binding_id": "B1",
                        "causal_role": "trigger_event_evidence",
                        "message_id": "m1",
                        "text_sha256": text_sha,
                        "required_source_span": "姐姐",
                    }
                ],
            }
        ],
        "authority": {
            "canonical_admission": False,
            "canonical_write": False,
            "supersession": False,
            "psb_rebind": False,
            "runtime_wiring": False,
            "provider_wiring": False,
            "production_cutover": False,
        },
    }


def test_lossless_correction_produces_successor_without_mutating_predecessor() -> None:
    source = preview()
    frozen = copy.deepcopy(source)
    result = build_successor(
        preview=source,
        raw_export=raw_export(),
        raw_sha256=RAW_SHA,
        manifest=manifest(),
    )

    assert source == frozen
    successor = result["successor_candidate"]
    payload = successor["proposed_canonical_payload"]
    assert payload["version_id"] == "v2-semantic-fidelity-preview"
    assert payload["predecessor_version_id"] == "v1"
    assert payload["content"]["event"] == "His older sister arrived."
    assert len(payload["provenance_refs"]) == 2
    correction_ref = payload["provenance_refs"][-1]
    assert correction_ref["source_type"] == "semantic-fidelity-correction"
    assert correction_ref["admission_metadata"]["authority_scope"] == (
        "PREP_ONLY_NO_ADMISSION"
    )
    assert result["semantic_fidelity"]["provenance_identity_verified"] is True
    assert result["semantic_fidelity"]["semantic_fidelity_verified"] is True
    assert all(value is False for value in result["authority"].values())


def test_semantic_attribute_loss_fails_closed() -> None:
    broken = manifest()
    broken["corrections"][0]["normalized_semantic_attribute"]["value"] = "UNSPECIFIED"
    with pytest.raises(
        SemanticFidelityCorrectionError,
        match="normalized semantics do not preserve source attribute",
    ):
        build_successor(
            preview=preview(),
            raw_export=raw_export(),
            raw_sha256=RAW_SHA,
            manifest=broken,
        )


def test_missing_raw_source_span_fails_closed() -> None:
    broken = manifest()
    broken["corrections"][0]["raw_evidence"][0]["required_source_span"] = "妹妹"
    with pytest.raises(
        SemanticFidelityCorrectionError,
        match="required source span missing",
    ):
        build_successor(
            preview=preview(),
            raw_export=raw_export(),
            raw_sha256=RAW_SHA,
            manifest=broken,
        )


def test_raw_export_digest_mismatch_fails_closed() -> None:
    with pytest.raises(SemanticFidelityCorrectionError, match="RAW export SHA mismatch"):
        build_successor(
            preview=preview(),
            raw_export=raw_export(),
            raw_sha256="f" * 64,
            manifest=manifest(),
        )


def test_historical_digest_mismatch_fails_closed() -> None:
    broken = manifest()
    broken["historical_candidate"]["canonical_digest"] = "e" * 64
    with pytest.raises(
        SemanticFidelityCorrectionError,
        match="historical canonical digest mismatch",
    ):
        build_successor(
            preview=preview(),
            raw_export=raw_export(),
            raw_sha256=RAW_SHA,
            manifest=broken,
        )


def test_deterministic_replay_is_exact() -> None:
    args = {
        "preview": preview(),
        "raw_export": raw_export(),
        "raw_sha256": RAW_SHA,
        "manifest": manifest(),
    }
    first = build_successor(**copy.deepcopy(args))
    second = build_successor(**copy.deepcopy(args))
    assert first == second
    assert first["deterministic_digest"] == second["deterministic_digest"]
