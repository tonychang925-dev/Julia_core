"""C1-R2.9 Legacy / provider reachability gates.

Protected contracts: REV2 Section 16/17, C-00, C-03, C-08, C-12.
Canonical mapping: C1 REV2 Section 14 / original C1-R2.10.

Primary rule:
    UNKNOWN FACT != XFAIL IMPLEMENTATION GAP.

Reachability and provider/deployment facts may be classified only with evidence.
If source or deployment evidence is absent, the correct test disposition is
PENDING (pytest skip), not strict xfail and not a fabricated PASS.

TC-ID: C1-R2.9-REACH-001 no zero-bypass claim without classified reachability map
TC-ID: C1-R2.9-REACH-002 classify surfaces only as ACTIVE/COMPAT/TEST-ONLY/DEAD/DELETE with evidence
TC-ID: C1-R2.9-PROVIDER-001 active production LLM provider source audit gate
TC-ID: C1-R2.9-STREAM-001 streaming protocol freeze requires provider audit evidence
TC-ID: C1-R2.9-AITHEME-001 ai_theme deployment/reachability facts require adapter audit evidence
TC-ID: C1-R2.9-LEGACY-001 confirmed legacy semantic pre-routing remains migration debt, not zero-bypass
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest


ROOT = Path(__file__).resolve().parents[2]

ReachabilityClass = Literal["ACTIVE", "COMPAT", "TEST-ONLY", "DEAD", "DELETE"]
VALID_REACHABILITY_CLASSES = {"ACTIVE", "COMPAT", "TEST-ONLY", "DEAD", "DELETE"}
PENDING_DISPOSITIONS = {"D-01", "D-02", "D-03", "D-04"}


@dataclass(frozen=True, slots=True)
class SurfaceClassification:
    surface: str
    path: str
    classification: ReachabilityClass
    evidence_terms: tuple[str, ...]
    reason: str

    def assert_evidence_present(self) -> None:
        file_path = ROOT / self.path
        assert file_path.exists(), f"Missing source evidence for {self.surface}: {self.path}"
        source = file_path.read_text(encoding="utf-8")
        missing = [term for term in self.evidence_terms if term not in source]
        assert not missing, f"Missing evidence terms for {self.surface}: {missing}"
        assert self.classification in VALID_REACHABILITY_CLASSES
        assert self.reason.strip()


EVIDENCE_CLASSIFIED_SURFACES: tuple[SurfaceClassification, ...] = (
    SurfaceClassification(
        surface="JuliaSession.process sync cognitive entrypoint",
        path="julia_core/runtime/julia_session.py",
        classification="ACTIVE",
        evidence_terms=("def process(", "return self._chat_impl(text, ctx)"),
        reason="Source shows the public sync cognitive entrypoint routes into _chat_impl on this branch.",
    ),
    SurfaceClassification(
        surface="JuliaSession.process_stream streaming cognitive entrypoint",
        path="julia_core/runtime/julia_session.py",
        classification="ACTIVE",
        evidence_terms=("async def process_stream", "self.provider.stream_async(messages)"),
        reason="Source shows a public streaming cognitive entrypoint; protocol details remain D-03 pending.",
    ),
    SurfaceClassification(
        surface="RuntimeCapabilityBridge used by JuliaSession",
        path="julia_core/runtime/julia_session.py",
        classification="ACTIVE",
        evidence_terms=("from julia_core.runtime.capability_bridge import get_capability_bridge", "self.capability = get_capability_bridge()"),
        reason="Source shows JuliaSession initializes RuntimeCapabilityBridge as its capability facade.",
    ),
    SurfaceClassification(
        surface="WorkflowRouter instantiated by JuliaSession",
        path="julia_core/runtime/julia_session.py",
        classification="ACTIVE",
        evidence_terms=("from julia_core.runtime.workflow_router import WorkflowRouter", "self.workflow_router = WorkflowRouter(self.capability)"),
        reason="Source shows runtime instantiation; separate C1-R2.2 tests cover semantic-routing debt.",
    ),
    SurfaceClassification(
        surface="Legacy chat E2E provider monkeypatches",
        path="tests/runtime/test_chat_e2e.py",
        classification="TEST-ONLY",
        evidence_terms=("sys.modules[\"providers.llm.deepseek_provider\"]", "fake_deepseek"),
        reason="The referenced provider replacement is inside tests and cannot prove production provider behavior.",
    ),
)


def _pending(disposition: str, reason: str) -> None:
    assert disposition in PENDING_DISPOSITIONS
    pytest.skip(f"PENDING {disposition}: {reason}")


# ── Reachability map guards ─────────────────────────────────────────────────


def test_reachability_classifications_use_only_allowed_labels_and_source_evidence():
    """TC-ID: C1-R2.9-REACH-002. A classification is valid only when evidence-backed."""
    assert EVIDENCE_CLASSIFIED_SURFACES
    for surface in EVIDENCE_CLASSIFIED_SURFACES:
        surface.assert_evidence_present()


def test_no_dead_or_delete_classification_exists_without_explicit_reachability_evidence():
    """TC-ID: C1-R2.9-REACH-002. No path may be declared DEAD/DELETE by assumption."""
    for surface in EVIDENCE_CLASSIFIED_SURFACES:
        if surface.classification in {"DEAD", "DELETE"}:
            surface.assert_evidence_present()
            assert "no production caller" in surface.reason.lower() or "delete authorized" in surface.reason.lower()


def test_no_zero_bypass_claim_without_complete_classified_reachability_map():
    """TC-ID: C1-R2.9-REACH-001. Exclusive-path claims require a completed kill/reachability map."""
    map_candidates = (
        ROOT / "docs" / "audit" / "JULIA_EXTERNAL_CAPABILITY_REACHABILITY_KILL_MAP.md",
        ROOT / "docs" / "project_control" / "JULIA_EXTERNAL_CAPABILITY_REACHABILITY_KILL_MAP.md",
    )
    existing = [path for path in map_candidates if path.exists()]
    if not existing:
        _pending("D-02", "no classified legacy/provider reachability kill map exists in this source tree")

    text = "\n".join(path.read_text(encoding="utf-8") for path in existing)
    required_columns = ("Reachable", "Executes", "Uses C-08", "Context OS", "Disposition")
    assert all(column in text for column in required_columns)
    assert "ZERO BYPASS" in text or "zero-bypass" in text.lower()


@pytest.mark.xfail(
    strict=True,
    reason="A-01/C-00: RuntimeCapabilityBridge.requires_tool is confirmed semantic pre-routing; migration debt pending R2-P4, not zero-bypass",
)
def test_confirmed_runtime_semantic_prerouting_prevents_zero_bypass_acceptance_claim():
    """TC-ID: C1-R2.9-LEGACY-001. Known active legacy semantic route remains xfail debt."""
    source = (ROOT / "julia_core" / "runtime" / "capability_bridge.py").read_text(encoding="utf-8")
    assert "def requires_tool" not in source
    assert "market_triggers" not in source
    assert "file_triggers" not in source


# ── Provider / streaming / deployment facts: PENDING, not xfail ─────────────


def test_active_production_llm_provider_source_audit_gate():
    """TC-ID: C1-R2.9-PROVIDER-001. Active provider source must be audited before freezing behavior."""
    provider_path = ROOT / "providers" / "llm" / "deepseek_provider.py"
    if not provider_path.exists():
        _pending("D-01", "JuliaSession references providers.llm.deepseek_provider, but active provider source is absent from this repo truth scope")

    source = provider_path.read_text(encoding="utf-8")
    required = ("def chat", "stream_async", "model", "provider")
    assert all(term in source for term in required)


def test_streaming_protocol_freeze_waits_for_provider_source_audit():
    """TC-ID: C1-R2.9-STREAM-001. Do not invent native/buffered streaming tool mechanics."""
    provider_path = ROOT / "providers" / "llm" / "deepseek_provider.py"
    if not provider_path.exists():
        _pending("D-03", "streaming native structured tool-call vs textual buffering mechanics lack provider source audit evidence")

    source = provider_path.read_text(encoding="utf-8")
    protocol_terms = {"tool_call", "function_call", "stream_async", "delta"}
    assert "stream_async" in source
    assert any(term in source for term in protocol_terms)


def test_provider_native_streaming_contract_test_does_not_assert_unknown_wire_facts():
    """TC-ID: C1-R2.9-STREAM-001. Existing tests must not freeze unknown provider wire behavior."""
    r26_source = (ROOT / "tests" / "runtime" / "test_c1_rev2_sync_stream_authority.py").read_text(encoding="utf-8")
    forbidden_claims = {
        "deepseek emits native tool events",
        "deepseek buffers first pass textual tool calls",
        "OpenAI-compatible stream guarantees tool_call chunking",
    }
    assert forbidden_claims.isdisjoint(r26_source.splitlines())


def test_ai_theme_deployment_reachability_facts_require_adapter_audit_evidence():
    """TC-ID: C1-R2.9-AITHEME-001. ai_theme deployment facts cannot be guessed from Julia tests."""
    handoff_candidates = (
        ROOT / "docs" / "integration" / "AI_THEME_ADAPTER_V1_HANDOFF.md",
        ROOT / "tests" / "fixtures" / "ai_theme_adapter" / "adapter_handoff_manifest.json",
    )
    existing = [path for path in handoff_candidates if path.exists()]
    if not existing:
        _pending("D-04", "no committed ai_theme adapter handoff/deployment audit artifact exists in Julia Core source tree")

    text = "\n".join(path.read_text(encoding="utf-8") for path in existing)
    required = ("endpoint", "health", "ready", "timeout", "schema_version", "source_records")
    assert all(term in text for term in required)
