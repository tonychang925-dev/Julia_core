#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.error
from collections import defaultdict
from pathlib import Path

from evaluate_jic_r0 import score_output
import run_jic_r0


def test_primary_cases_are_real_and_unlabeled() -> None:
    case_paths = sorted(Path(__file__).with_name("cases").glob("*.json"))
    assert len(case_paths) == 6
    families = defaultdict(int)
    for path in case_paths:
        case = json.loads(path.read_text(encoding="utf-8"))
        families[case["family"]] += 1
        serialized = json.dumps(case).lower()
        assert case["source"]["commit"]
        assert case["source"]["path"]
        assert case["source"]["record_identity"]
        assert case["source"]["as_of"]
        assert "expected" not in serialized
        assert "outcome" not in serialized
    assert set(families.values()) == {2}


def test_prompt_control_law() -> None:
    case = json.loads(Path(__file__).with_name("cases").joinpath("theme_lifecycle_ai_hardware_20260701.json").read_text())
    case["coverage"] = ["evaluation-only-label"]
    original = run_jic_r0.blob_at
    run_jic_r0.blob_at = lambda repo, commit, path: f"exact {path}@{commit}"
    try:
        prompts = [run_jic_r0.prompt_for(case, condition, Path("core"), Path("market")) for condition in "ABC"]
    finally:
        run_jic_r0.blob_at = original
    base = prompts[0]
    assert prompts[1].startswith(base)
    assert prompts[2].startswith(base)
    assert "# Historical cognition context" not in base
    assert "evaluation-only-label" not in prompts[0]
    assert "evaluation-only-label" not in prompts[1]
    assert "evaluation-only-label" not in prompts[2]


def test_regime_contrast_pair_has_visible_facts() -> None:
    case_dir = Path(__file__).with_name("cases")
    first = json.loads(case_dir.joinpath("theme_lifecycle_ai_hardware_20260701.json").read_text())
    second = json.loads(case_dir.joinpath("theme_lifecycle_ai_hardware_20260707.json").read_text())
    assert first["evidence_snapshot"]["subject_name"] == second["evidence_snapshot"]["subject_name"]
    assert first["evidence_snapshot"]["market_up_ratio"] >= 0.60
    assert second["evidence_snapshot"]["market_up_ratio"] <= 0.20
    assert first["evidence_snapshot"]["market_limit_up_count"] > 100
    assert second["evidence_snapshot"]["market_limit_up_count"] < 50


def test_evaluation_registry_covers_required_case_types() -> None:
    registry = json.loads(Path(__file__).with_name("case_registry.json").read_text(encoding="utf-8"))
    assert registry["evaluation_only"] is True
    coverage = [tag for tags in registry["case_coverage"].values() for tag in tags]
    assert coverage.count("regime_contrast_pair") >= 2
    assert "strong_counterevidence_case" in coverage
    assert "meaningful_missing_evidence_case" in coverage


def test_responses_raw_text_extraction() -> None:
    payload = {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "first"},
                    {"type": "output_text", "text": "second"},
                ],
            }
        ]
    }
    assert run_jic_r0.extract_response_text(payload) == "first\nsecond"


def test_responses_refusal_is_rejected() -> None:
    payload = {"output": [{"type": "message", "content": [{"type": "refusal", "refusal": "not allowed"}]}]}
    try:
        run_jic_r0.extract_response_text(payload)
    except ValueError as error:
        assert "refusal" in str(error)
    else:
        raise AssertionError("refusal content was accepted")


def test_frozen_evaluator_scores_structure() -> None:
    output = """## Current interpretation\nInsufficient evidence only.\n\n## Competing hypotheses\n- active hypothesis one\n- rejected hypothesis two\n- insufficient-evidence hypothesis three\n\n## Counterevidence\nMissing auction and volume may block confirmation.\n\n## Missing evidence\nMissing follower and regime data.\n\n## Falsifiers\n- if within next session volume expands\n- when follower breadth persists\n\n## Source and action boundary\nSubject=人工智能硬件; date=2026-07-01; source snapshot recorded; research only, not trading authorization.\n"""
    scores = score_output(output)["scores"]
    assert all(value == 1 for value in scores.values())


def test_conclusion_copy_is_detected_without_rejecting_boundary_words() -> None:
    output = """## Current interpretation\nInsufficient evidence only.\n\n## Competing hypotheses\n- active hypothesis one\n- rejected hypothesis two\n- insufficient-evidence hypothesis three\n\n## Counterevidence\nMissing auction and volume.\n\n## Missing evidence\nMissing follower and regime.\n\n## Falsifiers\n- if next session volume expands\n- when follower breadth persists\n\n## Source and action boundary\n2026-07-01; this is not a buy recommendation and not a sell recommendation.\n"""
    scores = score_output(output)["scores"]
    assert scores["strategy_transfer_without_conclusion_copy"] == 1
    copied = output.replace("active hypothesis one", "状态=发酵进场; operation=加仓龙头")
    assert score_output(copied)["scores"]["strategy_transfer_without_conclusion_copy"] == 0


def test_transport_failure_produces_blocked_artifact(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JIC_R0_PROVIDER", "openai")
    monkeypatch.setenv("JIC_R0_MODEL", "test-real-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setenv("JIC_R0_RUN_ID", "transport-test")
    monkeypatch.setattr(run_jic_r0, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(run_jic_r0, "validate_sources", lambda core, market: None)

    def fail(*args, **kwargs):
        return {
            "http_status": None,
            "elapsed_ms": 1,
            "response": {},
            "failure_kind": "url_error",
            "failure_detail": "gaierror",
        }

    monkeypatch.setattr(run_jic_r0, "call_openai", fail)
    monkeypatch.setattr(sys, "argv", ["run_jic_r0.py", "--core-repo", str(tmp_path), "--market-repo", str(tmp_path)])
    assert run_jic_r0.main() == 3
    blocked = json.loads((tmp_path / "results" / "run-transport-test" / "BLOCKED.json").read_text())
    assert blocked["status"] == "BLOCKED"
    assert blocked["last_request"]["failure_kind"] == "url_error"
    assert "test-secret" not in json.dumps(blocked)


def test_transport_exception_is_sanitized(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise urllib.error.URLError("temporary failure in name resolution")

    monkeypatch.setattr(run_jic_r0.urllib.request, "urlopen", fail)
    result = run_jic_r0.call_openai("prompt", "model", "secret")
    assert result["failure_kind"] == "url_error"
    assert result["response"] == {}
    assert "secret" not in json.dumps(result)
