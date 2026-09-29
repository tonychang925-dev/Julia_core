from __future__ import annotations

from typing import Sequence

import pytest

from julia_core.capability.models import (
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)


def _tool_observation(
    *,
    generation_id: str,
    provider: str,
    material: str,
) -> tuple[ToolResult, Evidence]:
    evidence_id = f"evidence-{generation_id}"
    evidence = Evidence(
        evidence_id=evidence_id,
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref=f"source-{generation_id}",
        observed_at="2026-09-29T00:00:00Z",
        content_ref=f"content-{generation_id}",
        provenance={
            "capability_id": "tool.observation.read",
            "provider": provider,
        },
    )
    tool_result = ToolResult(
        capability_call_id=f"call-{generation_id}",
        status=ToolResultStatus.SUCCESS,
        structured_output={
            "payload": {
                "material": material,
                "nested": {"generation_id": generation_id},
            }
        },
        evidence_refs=(evidence_id,),
        provider=provider,
    )
    return tool_result, evidence


def _market_observation(generation_id: str) -> tuple[ToolResult, Evidence]:
    return _tool_observation(
        generation_id=generation_id,
        provider="market",
        material="1251.24",
    )


def _research_observation(generation_id: str) -> tuple[ToolResult, Evidence]:
    evidence_id = f"evidence-{generation_id}"
    evidence = Evidence(
        evidence_id=evidence_id,
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref="src-1",
        observed_at="2026-09-29T00:00:00Z",
        content_ref=f"content-{generation_id}",
        provenance={
            "capability_id": "research.web.query",
            "provider": "research",
        },
    )
    tool_result = ToolResult(
        capability_call_id=f"call-{generation_id}",
        status=ToolResultStatus.SUCCESS,
        structured_output={
            "findings": [
                {
                    "material": "distinct-research-material",
                    "source_ref": "src-1",
                }
            ],
            "sources": [
                {
                    "ref": "src-1",
                    "url": "https://example.test/source-1",
                    "title": "Distinct Research Title",
                }
            ],
        },
        evidence_refs=(evidence_id,),
        provider="research",
    )
    return tool_result, evidence


def _project_sequence(
    observations: Sequence[tuple[ToolResult, Evidence]],
) -> CognitiveContextPackage:
    package = CognitiveContextPackage(
        conversation_id="conversation",
        turn_id="turn",
        generation_id="initial",
    )
    runtime = ContextExecutionRuntime()
    for index, (tool_result, evidence) in enumerate(observations):
        package = runtime.project_tool_result(
            parent_package=package,
            tool_result=tool_result,
            evidence=(evidence,),
            generation_id=f"generation-{index}",
        )
    return package


def test_research_only_real_structure_remains_visible():
    package = _project_sequence([_research_observation("research")])

    rendered = package.to_messages([], "query")[0]["content"]

    assert "distinct-research-material" in rendered
    assert "src-1" in rendered
    assert "Distinct Research Title" in rendered
    assert "https://example.test/source-1" in rendered
    assert "tool_result: projected_in_turn_evidence_ledger" not in rendered


@pytest.mark.parametrize("reverse", [False, True])
def test_market_and_research_material_remains_visible_in_both_orders(
    reverse: bool,
):
    observations = [
        _market_observation("market"),
        _research_observation("research"),
    ]
    if reverse:
        observations.reverse()
    package = _project_sequence(observations)

    rendered = package.to_messages([], "query")[0]["content"]

    assert "1251.24" in rendered
    assert "distinct-research-material" in rendered
    assert "src-1" in rendered
    assert "Distinct Research Title" in rendered
    assert "capability_id=research.web.query" in rendered
    assert "provider=market" in rendered
    assert "provider=research" in rendered


@pytest.mark.parametrize("reverse", [False, True])
def test_historical_material_survives_a_later_tool_result(reverse: bool):
    observations = [
        _tool_observation(
            generation_id="first",
            provider="provider-a",
            material="1251.24",
        ),
        _tool_observation(
            generation_id="second",
            provider="provider-b",
            material="research-material-7f31",
        ),
    ]
    if reverse:
        observations.reverse()

    parent = CognitiveContextPackage(
        conversation_id="conversation",
        turn_id="turn",
        generation_id="initial",
    )
    runtime = ContextExecutionRuntime()
    first_result, first_evidence = observations[0]
    first_package = runtime.project_tool_result(
        parent_package=parent,
        tool_result=first_result,
        evidence=(first_evidence,),
        generation_id="first",
    )
    second_result, second_evidence = observations[1]
    second_package = runtime.project_tool_result(
        parent_package=first_package,
        tool_result=second_result,
        evidence=(second_evidence,),
        generation_id="second",
    )

    rendered = second_package.to_messages([], "query")[0]["content"]

    assert "1251.24" in rendered
    assert "research-material-7f31" in rendered
    assert "generation_id=first" in rendered
    assert "generation_id=second" in rendered
    assert "provider=provider-a" in rendered
    assert "provider=provider-b" in rendered
    assert "source_ref=source-first" in rendered
    assert "source_ref=source-second" in rendered


def test_flattened_nested_mapping_remains_bounded_and_explicitly_truncated():
    payload = {
        f"field_{index}": "x" * 500
        for index in range(30)
    }
    tool_result, evidence = _tool_observation(
        generation_id="bounded",
        provider="provider-a",
        material="bounded-material",
    )
    tool_result.structured_output["payload"].update(payload)
    package = ContextExecutionRuntime().project_tool_result(
        parent_package=CognitiveContextPackage(
            conversation_id="conversation",
            turn_id="turn",
            generation_id="initial",
        ),
        tool_result=tool_result,
        evidence=(evidence,),
        generation_id="bounded",
    )

    rendered = package.to_messages([], "query")[0]["content"]

    assert "[evidence]" in rendered
    assert "bounded-material" in rendered
    assert "…[truncated]" in rendered
    assert len(package._render_frame("evidence", package.evidence_frame)) <= (
        CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
    )


def test_historical_scalar_survives_a_large_later_tool_result():
    first_result, first_evidence = _tool_observation(
        generation_id="market",
        provider="market",
        material="1251.24",
    )
    second_result, second_evidence = _tool_observation(
        generation_id="research",
        provider="research",
        material="latest-material",
    )
    second_result.structured_output["sources"] = [
        {
            "ref": f"source-{index}",
            "title": "research " * 200,
            "url": f"https://example.test/{index}",
        }
        for index in range(20)
    ]
    parent = CognitiveContextPackage(
        conversation_id="conversation",
        turn_id="turn",
        generation_id="initial",
    )
    runtime = ContextExecutionRuntime()
    first_package = runtime.project_tool_result(
        parent_package=parent,
        tool_result=first_result,
        evidence=(first_evidence,),
        generation_id="first",
    )
    second_package = runtime.project_tool_result(
        parent_package=first_package,
        tool_result=second_result,
        evidence=(second_evidence,),
        generation_id="second",
    )

    rendered = second_package.to_messages([], "query")[0]["content"]

    assert "1251.24" in rendered
    assert "latest-material" in rendered
    assert len(second_package._render_frame("evidence", second_package.evidence_frame)) <= (
        CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
    )


def test_all_historical_entries_survive_multiple_later_tool_results():
    observations = [
        _tool_observation(
            generation_id="market-state",
            provider="market",
            material="1251.24",
        ),
        _tool_observation(
            generation_id="market-analysis",
            provider="market",
            material="market-analysis-material",
        ),
        _tool_observation(
            generation_id="research",
            provider="research",
            material="latest-research-material",
        ),
    ]
    research_result, _ = observations[-1]
    research_result.structured_output["sources"] = [
        {
            "ref": f"source-{index}",
            "title": "research " * 200,
            "url": f"https://example.test/{index}",
        }
        for index in range(20)
    ]
    package = CognitiveContextPackage(
        conversation_id="conversation",
        turn_id="turn",
        generation_id="initial",
    )
    runtime = ContextExecutionRuntime()
    for index, (tool_result, evidence) in enumerate(observations):
        package = runtime.project_tool_result(
            parent_package=package,
            tool_result=tool_result,
            evidence=(evidence,),
            generation_id=f"generation-{index}",
        )

    rendered = package.to_messages([], "query")[0]["content"]

    assert "1251.24" in rendered
    assert "market-analysis-material" in rendered
    assert "latest-research-material" in rendered
    assert "generation_id=market-state" in rendered
    assert "generation_id=market-analysis" in rendered
    assert "generation_id=research" in rendered
    assert len(package._render_frame("evidence", package.evidence_frame)) <= (
        CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
    )


def test_flattened_mapping_terminates_on_nested_cycles():
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic

    rendered = CognitiveContextPackage()._render_value(
        cyclic,
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "…[truncated]" in rendered
    assert len(rendered) <= CognitiveContextPackage._RENDER_MAX_FRAME_CHARS


def test_flattened_sequence_terminates_on_nested_cycles():
    cyclic: list[object] = []
    cyclic.append(cyclic)

    rendered = CognitiveContextPackage()._render_value(
        cyclic,
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "…[truncated]" in rendered
    assert len(rendered) <= CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
