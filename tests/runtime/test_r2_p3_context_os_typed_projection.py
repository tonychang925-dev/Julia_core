"""R2-P3.0 typed Context OS capability projection acceptance overlay.

Protected contracts:
- C-03: all Core-controlled model-visible capability/control material routes
  through Context OS projection provenance.
- C-08: ToolResult is the execution outcome and remains distinct from
  CapabilityRequest / CapabilityCall.
- C-12: Evidence is cognition-supporting material, not ToolResult, Trace,
  Action, Identity, Persona, Relationship, durable Memory, or Continuity truth.
- ADR-037: capability evidence projection must not mutate identity/continuity
  authority surfaces.

Expected status before R2-P3 production:
- PASS only for legacy-boundary / identity-isolation invariants already true.
- strict-XFAIL for known P3 migration gaps.

Resolving phase: R2-P3.
"""

from __future__ import annotations

import inspect
from dataclasses import fields
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityResult,
    CapabilityStatus,
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus
from julia_core.capability.registry import CapabilityRegistry
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)


ROOT = Path(__file__).resolve().parents[2]


def _tool_result(
    call_id: str,
    *,
    status: ToolResultStatus = ToolResultStatus.SUCCESS,
    evidence_refs: tuple[str, ...] = (),
    output: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> ToolResult:
    return ToolResult(
        capability_call_id=call_id,
        status=status,
        structured_output=dict(output or {}),
        error=error,
        evidence_refs=evidence_refs,
        provider="local",
        schema_version="1.0",
    )


def _evidence(evidence_id: str, call_id: str, *, source_ref: str = "capability:file.read:provider:local") -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref=source_ref,
        observed_at="2026-08-27T00:00:00Z",
        content_ref=f"tool_result:{call_id}:structured_output",
        provenance={
            "capability_call_id": call_id,
            "capability_id": "file.read",
            "provider": "local",
        },
        integrity_metadata={"material_type": "provider_structured_output"},
        freshness="fresh",
        confidence=1.0,
        correlation_id=f"corr-{call_id}",
    )


def _rendered(delta: CognitiveContextPackage) -> str:
    return "\n".join(str(message.get("content", "")) for message in delta.to_messages([], ""))


def test_p3_context_os_accepts_canonical_tool_result_and_evidence_refs():
    """A. ToolResult/Evidence projection must preserve canonical IDs and provenance."""
    runtime = ContextExecutionRuntime()
    parent = CognitiveContextPackage(conversation_id="conv-p3", turn_id="turn-p3", generation_id="gen-before")
    evidence = _evidence("ev-call-a", "call-a")
    tool_result = _tool_result("call-a", evidence_refs=("ev-call-a",), output={"content": "observed fact"})

    hints = get_type_hints(ContextExecutionRuntime.project_tool_result)
    assert hints.get("tool_result") is not str

    delta = runtime.project_tool_result(
        parent_package=parent,
        tool_result=tool_result,
        evidence=[evidence],
        generation_id="gen-after",
    )

    assert delta.evidence_frame["tool_result"]["capability_call_id"] == "call-a"
    assert delta.evidence_frame["tool_result"]["status"] == ToolResultStatus.SUCCESS.value
    assert delta.evidence_frame["tool_result"]["evidence_refs"] == ["ev-call-a"]
    assert delta.evidence_frame["evidence"][0]["evidence_id"] == "ev-call-a"
    assert delta.evidence_frame["evidence"][0]["source_ref"] == "capability:file.read:provider:local"
    assert delta.evidence_frame["evidence"][0]["provenance"]["capability_call_id"] == "call-a"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "R2-P3/B: projection must associate artifacts by explicit call/evidence "
        "IDs, not by latest result/list order; typed projection API is not present yet"
    ),
)
def test_p3_projection_uses_exact_id_association_not_latest_artifact_order():
    """B. Multiple artifacts present: call A must project only call A evidence."""
    runtime = ContextExecutionRuntime()
    parent = CognitiveContextPackage(conversation_id="conv-p3", turn_id="turn-p3", generation_id="gen-before")
    ev_a = _evidence("ev-a", "call-a")
    ev_b = _evidence("ev-b", "call-b", source_ref="capability:file.search:provider:local")
    result_a = _tool_result("call-a", evidence_refs=("ev-a",), output={"content": "A"})
    result_b = _tool_result("call-b", evidence_refs=("ev-b",), output={"content": "B"})

    delta = runtime.project_tool_result(
        parent_package=parent,
        tool_result=result_a,
        evidence=[ev_b, ev_a],
        available_tool_results=[result_b, result_a],
        generation_id="gen-after-a",
    )

    rendered = _rendered(delta)
    assert "call-a" in rendered
    assert "ev-a" in rendered
    assert "call-b" not in rendered
    assert "ev-b" not in rendered


@pytest.mark.parametrize(
    "status",
    [
        AuthorizationStatus.DENY,
        AuthorizationStatus.REQUIRE_CONFIRMATION,
        AuthorizationStatus.REQUIRE_ELEVATION,
        AuthorizationStatus.UNAVAILABLE,
    ],
)
def test_p3_authorization_only_outcomes_project_without_execution_artifacts(status: AuthorizationStatus):
    """C. Non-ALLOW authorization may be visible, but must not synthesize execution artifacts."""
    decision = AuthorizationDecision(decision=status, scope="file.read", reason=f"{status.value} for test")
    delta = ContextExecutionRuntime().project_authorization_outcome(
        parent_package=CognitiveContextPackage(conversation_id="conv", turn_id="turn", generation_id="gen-before"),
        authorization_decision=decision,
        generation_id="gen-auth",
    )

    frame = delta.evidence_frame.get("authorization_outcome", {})
    assert frame["decision"] == status.value
    assert frame["capability_call_id"] is None
    assert frame["tool_result"] is None
    assert frame["evidence"] == []
    assert "TOOL_OBSERVATION" not in _rendered(delta)


@pytest.mark.parametrize(
    "status,error",
    [
        (ToolResultStatus.UNAVAILABLE, {"code": "provider_unhealthy", "message": "provider unavailable"}),
        (ToolResultStatus.ERROR, {"code": "provider_exception", "message": "provider failed"}),
    ],
)
def test_p3_execution_failure_projects_structured_non_success_without_observation_evidence(
    status: ToolResultStatus,
    error: dict[str, str],
):
    """D. Execution failures after ALLOW are ToolResult outcomes, not Evidence."""
    result = _tool_result("call-failure", status=status, evidence_refs=(), error=error)
    delta = ContextExecutionRuntime().project_tool_result(
        parent_package=CognitiveContextPackage(conversation_id="conv", turn_id="turn", generation_id="gen-before"),
        tool_result=result,
        evidence=[],
        generation_id="gen-failure",
    )

    frame = delta.evidence_frame["tool_result"]
    assert frame["status"] == status.value
    assert frame["error"]["code"] == error["code"]
    assert frame["evidence_refs"] == []
    assert delta.evidence_frame.get("evidence", []) == []
    assert "TOOL_OBSERVATION" not in _rendered(delta)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "R2-P3/E: JuliaSession still appends core-owned retry guidance directly "
        "as synthetic messages instead of Context OS projection"
    ),
)
def test_p3_retry_control_material_is_context_os_projected_not_direct_message_append():
    """E. Retry/control guidance is Core control material, not external Evidence."""
    session_source = (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()
    context_source = (ROOT / "julia_core" / "runtime" / "context_execution_runtime.py").read_text()

    assert "[系统提示]" not in session_source
    assert "messages.append({\"role\": \"user\"" not in session_source
    assert "project_control_guidance" in context_source or "control_frame" in context_source


def test_p3_capability_frame_canonical_state_is_structured_not_truncated_text():
    """F. Text rendering may exist downstream, but canonical frame is structured."""

    class _Capability:
        def __init__(self):
            self.registry = CapabilityRegistry()
            self.registry.register_definition(CapabilityDefinition(
                name="file.read",
                description="Read file contents from the local filesystem",
                layer=CapabilityLayer.KNOWLEDGE,
                provider="local",
                permission_scope="file.read",
                input_schema={"path": "file path"},
                status=CapabilityStatus.AVAILABLE,
            ))
            self.registry.register_definition(CapabilityDefinition(
                name="file.search",
                description="Search for files by name pattern",
                layer=CapabilityLayer.KNOWLEDGE,
                provider="local",
                permission_scope="file.read",
                input_schema={"pattern": "search pattern"},
                status=CapabilityStatus.AVAILABLE,
            ))

        def tool_manifest(self):
            return "file.read: Read file\nfile.search: Search files"

    class _Persona:
        def get_traits_for_injection(self):
            return ""

    class _Session:
        persona = _Persona()
        capability = _Capability()

        def _load_recent_experiences(self):
            return ""

        def _resolve_market_context(self, _text):
            return ""

    pkg = ContextExecutionRuntime(_Session()).prepare(
        conversation_id="conv",
        turn_id="turn",
        user_text="read file",
        history=[],
    )

    entries = pkg.capability_frame["available_tools"]
    assert isinstance(entries, list)
    assert entries
    assert all(isinstance(entry, dict) for entry in entries)
    assert {"capability_id", "description", "input_schema"}.issubset(entries[0])
    assert "[:600]" not in inspect.getsource(ContextExecutionRuntime.prepare)


def test_p3_legacy_capability_result_remains_compatibility_not_canonical_tool_result():
    """G. Do not mutate CapabilityResult into canonical ToolResult/Evidence for test convenience."""
    legacy_fields = {field.name for field in fields(CapabilityResult)}

    assert "capability_name" in legacy_fields
    assert "data" in legacy_fields
    assert "evidence" in legacy_fields
    assert "structured_output" not in legacy_fields
    assert "evidence_refs" not in legacy_fields


def test_p3_capability_projection_still_does_not_mutate_identity_or_continuity_authority():
    """G / ADR-037. Preserve T-CX-04 identity, memory, relationship, continuity isolation."""
    delta = ContextExecutionRuntime().project_tool_result(
        parent_package=CognitiveContextPackage(conversation_id="conv", turn_id="turn", generation_id="gen-before"),
        tool_result="legacy capability observation",
        generation_id="gen-after",
    )

    assert delta.identity_frame == {}
    assert delta.experience_frame == {}
    assert delta.diary_frame == {}
    assert delta.continuity_frame == {}
    assert delta.projection_metadata.get("identity_updated") is not True
    assert delta.projection_metadata.get("memory_updated") is not True
    assert delta.projection_metadata.get("relationship_updated") is not True
    assert delta.projection_metadata.get("continuity_authority_updated") is not True
