from __future__ import annotations

import json
from pathlib import Path
from dataclasses import replace
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


def _real_observation(
    *,
    generation_id: str,
    provider: str,
    capability_id: str,
    structured_output: dict[str, object],
    source_ref: str,
) -> tuple[ToolResult, Evidence]:
    evidence_id = f"evidence-{generation_id}"
    evidence = Evidence(
        evidence_id=evidence_id,
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref=source_ref,
        observed_at="2026-09-29T00:00:00Z",
        content_ref=f"content-{generation_id}",
        provenance={
            "capability_id": capability_id,
            "provider": provider,
        },
    )
    tool_result = ToolResult(
        capability_call_id=f"call-{generation_id}",
        status=ToolResultStatus.SUCCESS,
        structured_output=structured_output,
        evidence_refs=(evidence_id,),
        provider=provider,
    )
    return tool_result, evidence


def _real_market_observation() -> tuple[ToolResult, Evidence]:
    artifact = Path("docs/evidence/RD1_P2_I2C_REWORK_DIAGNOSTIC_E2E_20260929.json")
    event = next(
        event
        for event in json.loads(artifact.read_text())["trace"]
        if event.get("event") == "market.result"
        and event.get("structured_output", {}).get("capability_id")
        == "market.state.read"
        and event.get("structured_output", {}).get("data_state") == "READY"
    )
    return _real_observation(
        generation_id="real-market",
        provider="market",
        capability_id="market.state.read",
        structured_output=event["structured_output"],
        source_ref="capability:market.state.read:provider:market",
    )


def _real_research_observation() -> tuple[ToolResult, Evidence]:
    artifact = Path("docs/evidence/RD1_P2_I2C_NATURAL_E2E_EVIDENCE_20260929.json")
    event = next(
        event
        for event in json.loads(artifact.read_text())["trace"]
        if event.get("event") == "research.result"
        and event.get("structured_output", {}).get("findings")
    )
    structured_output = event["structured_output"]
    finding = structured_output["findings"][0]
    source_ref = finding["source_ref"]
    assert any(
        source.get("ref") == source_ref for source in structured_output["sources"]
    )
    return _real_observation(
        generation_id="real-research",
        provider="research",
        capability_id="research.web.query",
        structured_output=structured_output,
        source_ref=source_ref,
    )


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


def test_real_research_only_structure_remains_source_bound():
    package = _project_sequence([_real_research_observation()])

    rendered = package.to_messages([], "query")[0]["content"]

    assert "AI+机器人 小场景跑出大订单" in rendered
    assert (
        "src_8ae9e184414c44c79a5c61770519cdcf31319434f81f704529ec12b09ff421b3"
        in rendered
    )
    assert "https://paper.cnstock.com/html/2026-09/24/content_2272401.htm" in rendered
    assert "AI+机器人 小场景跑出大订单 具身智能落地走向实处" in rendered


@pytest.mark.parametrize("reverse", [False, True])
def test_real_market_and_research_remain_visible_in_both_orders(reverse: bool):
    observations = [
        _real_market_observation(),
        _real_research_observation(),
    ]
    if reverse:
        observations.reverse()
    package = _project_sequence(observations)

    rendered = package.to_messages([], "query")[0]["content"]

    assert "2357" in rendered
    assert "AI+机器人 小场景跑出大订单" in rendered
    assert (
        "src_8ae9e184414c44c79a5c61770519cdcf31319434f81f704529ec12b09ff421b3"
        in rendered
    )
    assert "https://paper.cnstock.com/html/2026-09/24/content_2272401.htm" in rendered
    assert "AI+机器人 小场景跑出大订单 具身智能落地走向实处" in rendered
    assert "capability_id=market.state.read" in rendered
    assert "capability_id=research.web.query" in rendered


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
    payload = {f"field_{index}": "x" * 500 for index in range(30)}
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
    assert len(
        second_package._render_frame("evidence", second_package.evidence_frame)
    ) <= (CognitiveContextPackage._RENDER_MAX_FRAME_CHARS)


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


def test_latest_evidence_is_deduplicated_but_lineage_remains_visible():
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
    extra_evidence = tuple(
        Evidence(
            evidence_id=f"evidence-current-{index}",
            source_type=EvidenceSourceType.TOOL_OBSERVATION,
            source_ref=f"source-current-{index}",
            observed_at="2026-09-29T00:00:00Z",
            content_ref=f"content-current-{index}",
            provenance={
                "capability_id": "research.web.query",
                "provider": "research",
            },
        )
        for index in range(20)
    )
    second_result = replace(
        second_result,
        evidence_refs=tuple(evidence.evidence_id for evidence in extra_evidence),
    )
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
        evidence=extra_evidence,
        generation_id="second",
    )

    rendered = second_package.to_messages([], "query")[0]["content"]

    assert "1251.24" in rendered
    assert "latest-material" in rendered
    assert "evidence-current-0" in rendered


def test_cyclic_structured_output_reaches_bounded_renderer():
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic
    tool_result, evidence = _tool_observation(
        generation_id="cyclic",
        provider="provider",
        material="cyclic-material",
    )
    tool_result.structured_output["payload"]["cycle"] = cyclic
    package = ContextExecutionRuntime().project_tool_result(
        parent_package=CognitiveContextPackage(
            conversation_id="conversation",
            turn_id="turn",
            generation_id="initial",
        ),
        tool_result=tool_result,
        evidence=(evidence,),
        generation_id="cyclic",
    )

    rendered = package.to_messages([], "query")[0]["content"]

    assert "cyclic-material" in rendered
    assert "…[truncated]" in rendered
    assert len(package._render_frame("evidence", package.evidence_frame)) <= (
        CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
    )


def test_flattened_traversal_does_not_let_first_branch_starve_sibling():
    value = {
        "a_big": {f"key_{index}": str(index) for index in range(100)},
        "z_status": "SUCCESS",
    }

    rendered = CognitiveContextPackage()._render_value(
        value,
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "z_status=SUCCESS" in rendered
    assert "…[truncated]" in rendered


def test_flattened_empty_nested_containers_remain_visible():
    rendered = CognitiveContextPackage()._render_value(
        {"data": {}, "items": [], "present": "yes"},
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "data={  }" in rendered
    assert "items=[]" in rendered
    assert "present=yes" in rendered


def test_flattened_mapping_paths_escape_key_components():
    rendered = CognitiveContextPackage()._render_value(
        {"a.b[0]\nfake": "escaped-path"},
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "a%2Eb%5B0%5D%0Afake=escaped-path" in rendered


def test_flattened_root_sequence_enumeration_is_bounded():
    leaves, omitted = CognitiveContextPackage()._flatten_bounded_leaves(
        [str(index) for index in range(10_000)],
        root_sequence=True,
    )

    assert omitted is True
    assert len(leaves) <= CognitiveContextPackage._RENDER_MAX_ITEMS * 8


def test_flattened_traversal_reserves_slots_for_nested_siblings():
    value = {
        "a_big": {f"key_{index}": str(index) for index in range(100)},
        "b_branch": {"note": "hello"},
        "z_branch": {"status": "SUCCESS"},
    }

    rendered = CognitiveContextPackage()._render_value(
        value,
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "b_branch.note=hello" in rendered
    assert "z_branch.status=SUCCESS" in rendered
    assert "…[truncated]" in rendered


def test_selected_leaves_share_render_budget():
    value = {
        **{f"field_{index}": "x" * 5_000 for index in range(4)},
        "z_status": "SUCCESS",
    }

    rendered = CognitiveContextPackage()._render_value(
        value,
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "z_status=SUCCESS" in rendered
    assert "…[truncated]" in rendered
    assert len(rendered) <= CognitiveContextPackage._RENDER_MAX_FRAME_CHARS


def test_flattened_explicit_null_and_empty_string_leaves_remain_visible():
    rendered = CognitiveContextPackage()._render_value(
        {"status": "SUCCESS", "payload": None, "empty": ""},
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "status=SUCCESS" in rendered
    assert "payload=None" in rendered
    assert "empty=" in rendered


def test_first_projection_does_not_reserve_empty_ledger_budget():
    tool_result, evidence = _tool_observation(
        generation_id="single",
        provider="provider",
        material="material",
    )
    tool_result = replace(
        tool_result,
        structured_output={
            "alpha": "A" * 1_600,
            "beta": "B" * 1_600,
        },
    )
    package = ContextExecutionRuntime().project_tool_result(
        parent_package=CognitiveContextPackage(
            conversation_id="conversation",
            turn_id="turn",
            generation_id="initial",
        ),
        tool_result=tool_result,
        evidence=(evidence,),
        generation_id="single",
    )

    rendered = package.to_messages([], "query")[0]["content"]

    assert "A" * 500 in rendered
    assert "B" * 500 in rendered


def test_short_sequence_items_use_available_budget():
    rendered = CognitiveContextPackage()._render_value(
        [f"v{index}" for index in range(20)],
        depth=0,
        char_budget=1_000,
    )

    assert "v0" in rendered
    assert "v19" in rendered
    assert "…[truncated]" not in rendered


def test_tiny_nonempty_flattened_containers_signal_truncation():
    package = CognitiveContextPackage()

    mapping = package._render_value(
        {"field": "value"},
        depth=package._RENDER_MAX_DEPTH,
        char_budget=2,
    )
    sequence = package._render_value(
        ["value"],
        depth=package._RENDER_MAX_DEPTH,
        char_budget=2,
    )

    assert mapping.startswith("…")
    assert sequence.startswith("…")
    assert mapping != "{}"
    assert sequence != "[]"


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


def test_flattened_mapping_marks_omitted_leaf_quota():
    value = {f"field_{index}": str(index) for index in range(21)}

    rendered = CognitiveContextPackage()._render_value(
        value,
        depth=CognitiveContextPackage._RENDER_MAX_DEPTH,
        char_budget=CognitiveContextPackage._RENDER_MAX_FRAME_CHARS,
    )

    assert "…[truncated]" in rendered
    assert len(rendered) <= CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
