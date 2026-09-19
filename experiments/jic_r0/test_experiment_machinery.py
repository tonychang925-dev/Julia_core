#!/usr/bin/env python3
from __future__ import annotations

import json
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
    case = json.loads(Path(__file__).with_name("cases").joinpath("theme_lifecycle_9065632_20260407.json").read_text())
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


def test_frozen_evaluator_scores_structure() -> None:
    output = """## Current interpretation\nInsufficient evidence only.\n\n## Competing hypotheses\n- active hypothesis one\n- rejected hypothesis two\n- insufficient-evidence hypothesis three\n\n## Counterevidence\nMissing auction and volume may block confirmation.\n\n## Missing evidence\nMissing follower and regime data.\n\n## Falsifiers\n- if within next session volume expands\n- when follower breadth persists\n\n## Source and action boundary\nResearch only.\n"""
    scores = score_output(output)["scores"]
    assert all(value == 1 for value in scores.values())
