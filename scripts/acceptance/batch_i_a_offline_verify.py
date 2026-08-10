#!/usr/bin/env python3
"""Batch I acceptance matrix verifier.

Non-production verification only. This script validates the single acceptance
matrix, contract/document presence, runtime gating discipline, and fixture
completeness. It intentionally does not call model providers, Voice/S2S,
Electron, or GPU services. It allows FULL_PASS only when runtime_evidence is
recorded in the matrix; offline-only ATs must remain RUNTIME_REQUIRED.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/acceptance/batch_i_a_acceptance_matrix.json"
WBS = ROOT / "docs/architecture/JULIA_CORE_UNIFIED_ARCHITECTURE_WORK_BREAKDOWN_v1.1_FREEZE_CANDIDATE.md"
UNIFIED = ROOT / "docs/architecture/JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md"
EVIDENCE = ROOT / "docs/architecture/FINAL_ACCEPTANCE_EVIDENCE.md"
FIXTURES = ROOT / "docs/acceptance/fixtures/AT13_AT17_RUNTIME_FIXTURES.md"
BLOCKERS = ROOT / "docs/acceptance/BATCH_I_A_RUNTIME_BLOCKERS.md"

VALID_STATUS = {"OFFLINE_PASS", "RUNTIME_REQUIRED", "FULL_PASS", "FAIL", "BLOCKED"}
REQUIRED_FIELDS = {
    "at_id",
    "acceptance_claim",
    "frozen_contracts",
    "owning_convergence_phase",
    "offline_component",
    "runtime_component",
    "gpu_required",
    "voice_required",
    "cross_provider_required",
    "fixture_scenario",
    "evidence_artifact",
    "offline_result",
    "runtime_result",
    "final_status",
    "known_blocker",
    "defect_reference",
}
CONTRACT_FILES = {
    "C-00": "docs/architecture/C-00_COGNITIVE_BOUNDARY_CONTRACT.md",
    "C-01": "docs/architecture/C-01_RUNTIME_EXECUTION_CONTRACT.md",
    "C-02": "docs/architecture/C-02_CONVERSATION_AUTHORITY_CONTRACT.md",
    "C-03": "docs/architecture/C-03_CONTEXT_OS_CONTRACT.md",
    "C-04": "docs/architecture/C-04_IDENTITY_PERSONA_CONTRACT.md",
    "C-05": "docs/architecture/C-05_MEMORY_OS_CONTRACT.md",
    "C-06": "docs/architecture/C-06_CONTINUITY_OS_CONTRACT.md",
    "C-07": "docs/architecture/C-07_MODEL_PROVIDER_CONTRACT.md",
    "C-08": "docs/architecture/C-08_CAPABILITY_TOOL_CONTRACT.md",
    "C-09": "docs/architecture/C-09_ALIGNMENT_CONTRACT.md",
    "C-10": "docs/architecture/C-10_GATEWAY_CLIENT_CONTRACT.md",
    "C-11": "docs/architecture/C-11_VOICE_MEDIA_CONTRACT.md",
    "C-12": "docs/architecture/C-12_EVIDENCE_ACTION_TRACE_CONTRACT.md",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def load_json(path: Path) -> Any:
    if not path.exists():
        fail(f"missing {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8")


def validate_matrix() -> None:
    data = load_json(MATRIX)
    ats = data.get("ats")
    if not isinstance(ats, list):
        fail("matrix ats must be a list")
    if len(ats) != 17:
        fail(f"matrix must contain 17 ATs, found {len(ats)}")
    expected_ids = [f"AT-{i:02d}" for i in range(1, 18)]
    actual_ids = [item.get("at_id") for item in ats]
    if actual_ids != expected_ids:
        fail(f"AT order/id mismatch: {actual_ids}")

    for item in ats:
        at_id = item["at_id"]
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            fail(f"{at_id} missing fields: {sorted(missing)}")
        for key in ("offline_result", "runtime_result", "final_status"):
            if item[key] not in VALID_STATUS:
                fail(f"{at_id} invalid {key}: {item[key]}")
        if item["final_status"] == "FULL_PASS" and not item.get("runtime_evidence"):
            fail(f"{at_id} marked FULL_PASS without runtime_evidence")
        if item["runtime_result"] == "FULL_PASS" and item["final_status"] != "FULL_PASS":
            fail(f"{at_id} runtime_result FULL_PASS but final_status is {item['final_status']}")
        if not item["frozen_contracts"]:
            fail(f"{at_id} has no frozen contract mapping")
        for contract in item["frozen_contracts"]:
            if contract not in CONTRACT_FILES:
                fail(f"{at_id} references unknown contract {contract}")
            if not (ROOT / CONTRACT_FILES[contract]).exists():
                fail(f"{at_id} contract file missing: {contract}")
        if not str(item["offline_component"]).strip() or not str(item["runtime_component"]).strip():
            fail(f"{at_id} must decompose offline/runtime components")
        if item["at_id"] in {"AT-13", "AT-14", "AT-15", "AT-16", "AT-17"}:
            if item["runtime_result"] == "FULL_PASS" and not item.get("runtime_evidence"):
                fail(f"{at_id} high-order runtime AT FULL_PASS requires runtime_evidence")
    ok("matrix contains AT-01..AT-17 with required fields and gated FULL_PASS discipline")


def validate_contract_docs() -> None:
    for contract, rel in CONTRACT_FILES.items():
        path = ROOT / rel
        if not path.exists():
            fail(f"missing frozen contract {contract}: {rel}")
    ok("C-00 through C-12 contract files exist")

    unified = read(UNIFIED)
    wbs = read(WBS)
    for i in range(1, 18):
        at_id = f"AT-{i:02d}"
        if at_id not in unified and at_id not in wbs:
            fail(f"{at_id} definition missing from architecture docs")
    ok("AT-01 through AT-17 definitions are present in architecture/WBS docs")


def validate_existing_evidence_discipline() -> None:
    text = read(EVIDENCE)
    if "AT-01~AT-17 ALL PASS" not in text:
        fail("FINAL_ACCEPTANCE_EVIDENCE must record AT-01~AT-17 ALL PASS after final runtime acceptance")
    if "julia_core aef5c4d" not in text:
        fail("FINAL_ACCEPTANCE_EVIDENCE must record baseline aef5c4d")
    if "6/6 applicable model-visible frames traced" not in text:
        fail("FINAL_ACCEPTANCE_EVIDENCE must use precise AT-17 applicable-frame wording")
    if "ContinuityFrame not projected in this scenario" not in text:
        fail("FINAL_ACCEPTANCE_EVIDENCE must explain non-projected ContinuityFrame")
    for at in ("AT-13", "AT-14", "AT-15", "AT-16", "AT-17"):
        if at not in text:
            fail(f"FINAL_ACCEPTANCE_EVIDENCE missing {at}")
    ok("final evidence map records all-pass baseline and precise AT-17 wording")


def validate_fixture_docs() -> None:
    fixture = read(FIXTURES)
    blockers = read(BLOCKERS)
    for token in ["AT-13", "AT-14", "AT-15", "AT-16", "AT-17"]:
        if token not in fixture:
            fail(f"fixture doc missing {token}")
    for token in ["RA-01", "RA-02", "RA-03", "RA-04", "RA-05", "RA-06", "RA-07"]:
        if token not in blockers:
            fail(f"runtime blocker list missing {token}")
    required_fixture_terms = [
        "event:",
        "meaning_at_time:",
        "experiential_significance:",
        "concrete_anchors:",
        "transformation:",
        "relationship_consequence:",
        "later_reinterpretation:",
        "A. Long irrelevant context",
        "B. Short dense context",
        "C. Structured causal context",
        "D. Full raw context",
        "Unauthorized request",
        "Authorized third-party acceptance",
        "Forged authorization rejection",
        "Context Source Completeness",
    ]
    for term in required_fixture_terms:
        if term not in fixture:
            fail(f"fixture doc missing required term: {term}")
    ok("AT-13~AT-17 fixtures and RA blocker list are complete at document level")


def validate_context_source_contract_terms() -> None:
    c03 = read(ROOT / CONTRACT_FILES["C-03"])
    c12 = read(ROOT / CONTRACT_FILES["C-12"])
    combined = c03 + "\n" + c12
    terms = ["package", "frame", "source", "provenance", "trace"]
    missing = [term for term in terms if term.lower() not in combined.lower()]
    if missing:
        fail(f"C-03/C-12 missing source/provenance terms: {missing}")
    ok("C-03/C-12 contain package/frame/source/provenance/trace support terms")


def validate_git_production_change_boundary() -> None:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail(f"git status failed: {result.stderr}")
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    production_like = []
    allowed_prefixes = (
        "docs/acceptance/",
        "scripts/acceptance/",
        "docs/architecture/JULIA_CORE_UNIFIED_ARCHITECTURE_WORK_BREAKDOWN_v1.0.md",
        "docs/architecture/JULIA_CORE_UNIFIED_ARCHITECTURE_WORK_BREAKDOWN_v1.1_FREEZE_CANDIDATE.md",
        "docs/architecture/FINAL_ACCEPTANCE_EVIDENCE.md",
        "data/events/",
    )
    for line in lines:
        path = line[3:] if len(line) > 3 else line
        if not path.startswith(allowed_prefixes):
            production_like.append(line)
    if production_like:
        fail("unexpected production-like working tree changes:\n" + "\n".join(production_like))
    ok("working tree changes are limited to docs/acceptance, scripts/acceptance, or pre-existing non-production artifacts")


def main() -> None:
    validate_matrix()
    validate_contract_docs()
    validate_existing_evidence_discipline()
    validate_fixture_docs()
    validate_context_source_contract_terms()
    validate_git_production_change_boundary()
    print("\nBATCH_I_ACCEPTANCE_MATRIX_VERIFY: PASS")


if __name__ == "__main__":
    main()
