"""R2-P3.2.3A capability control projection authority gate.

CapabilityPreAuthorizationFailure is a NON-CANONICAL runtime control fact,
NOT Evidence. It must be projected through a dedicated control frame (not
evidence_frame), be turn/generation scoped, and must not mutate
identity/persona/relationship/durable-memory/continuity authority.

These tests are strict-XFAIL until the production projection seam exists.
"""

from __future__ import annotations

import pytest

from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)


def _project(reason: str, capability_id: str = "no.such.capability"):
    return ContextExecutionRuntime().project_capability_resolution_failure(
        parent_package=CognitiveContextPackage(conversation_id="c", turn_id="t", generation_id="g"),
        capability_id=capability_id,
        reason=reason,
        generation_id="g2",
    )


def test_control_projection_unknown_is_structured():
    delta = _project("UNKNOWN")
    frame = delta.control_frame
    assert frame["kind"] == "capability_resolution_failure"
    assert frame["capability_id"] == "no.such.capability"
    assert frame["reason"] == "UNKNOWN"


def test_control_projection_disabled_is_structured():
    delta = _project("DISABLED", capability_id="file.disabled")
    frame = delta.control_frame
    assert frame["kind"] == "capability_resolution_failure"
    assert frame["reason"] == "DISABLED"


def test_control_projection_is_not_evidence_and_is_authority_isolated():
    delta = _project("UNKNOWN")
    # Not placed in evidence_frame; no ToolResult / authorization_outcome.
    assert delta.evidence_frame == {}
    assert delta.identity_frame == {}
    assert delta.experience_frame == {}
    assert delta.diary_frame == {}
    assert delta.continuity_frame == {}
    assert delta.projection_metadata.get("identity_updated") is not True
    assert delta.projection_metadata.get("memory_updated") is not True
    assert delta.projection_metadata.get("relationship_updated") is not True


def test_control_projection_renders_deterministically_without_tool_observation():
    delta = _project("UNKNOWN")
    rendered = "\n".join(str(m.get("content", "")) for m in delta.to_messages([], ""))
    assert "TOOL_OBSERVATION" not in rendered
    assert "capability_resolution_failure" in rendered
    assert "no.such.capability" in rendered
    assert "UNKNOWN" in rendered


def _parent() -> CognitiveContextPackage:
    return CognitiveContextPackage(conversation_id="c", turn_id="t", generation_id="g")


def test_control_projection_requires_parent_package():
    with pytest.raises(ValueError):
        ContextExecutionRuntime().project_capability_resolution_failure(
            parent_package=None,
            capability_id="no.such.capability",
            reason="UNKNOWN",
            generation_id="g2",
        )


def test_control_projection_requires_generation_id():
    with pytest.raises(ValueError):
        ContextExecutionRuntime().project_capability_resolution_failure(
            parent_package=_parent(),
            capability_id="no.such.capability",
            reason="UNKNOWN",
            generation_id="",
        )


def test_control_projection_rejects_blank_generation_id():
    with pytest.raises(ValueError):
        ContextExecutionRuntime().project_capability_resolution_failure(
            parent_package=_parent(),
            capability_id="no.such.capability",
            reason="UNKNOWN",
            generation_id="   ",
        )
